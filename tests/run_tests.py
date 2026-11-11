"""Kiểm thử 40 ca. `--validate-only` chỉ kiểm tra cấu trúc; `--live` chạy hệ thống thật.

Không dùng expected_action để giả lập kết quả. Kết quả PASS chỉ từ pipeline thực.
"""
import argparse
import contextlib
import io
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QUERY_FILE = ROOT / 'tests/queries/test_queries.json'
RESULT_DIR = ROOT / 'tests/results'
VALID_ROLES = {'SinhVien', 'GiangVien', 'QuanTri'}
CLASS_ROLES = {'Public': VALID_ROLES, 'Internal': {'GiangVien','QuanTri'}, 'Restricted': {'QuanTri'}}


def load_and_validate(path: Path):
    cases = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(cases, list):
        raise ValueError('test_queries.json phải là JSON array')
    seen = set()
    for i, case in enumerate(cases, 1):
        for field in ('test_id','category','role','query','target_doc_id','target_classification','expected_action','expected_retrieval_success'):
            if field not in case:
                raise ValueError(f'Ca {i} thiếu {field}')
        if case['test_id'] in seen:
            raise ValueError(f'Trùng test_id: {case["test_id"]}')
        seen.add(case['test_id'])
        if case['role'] not in VALID_ROLES:
            raise ValueError(f'Vai trò không hợp lệ: {case["test_id"]}')
        if case['target_classification'] not in CLASS_ROLES:
            raise ValueError(f'Phân loại không hợp lệ: {case["test_id"]}')
        allowed = case['role'] in CLASS_ROLES[case['target_classification']]
        if case['expected_action'] != ('ALLOW' if allowed else 'DENY'):
            raise ValueError(f'Expected_action sai RBAC: {case["test_id"]}')
        if case['expected_retrieval_success'] is not allowed:
            raise ValueError(f'Expected_retrieval_success sai RBAC: {case["test_id"]}')
        prefix = {'Public':'P','Internal':'I','Restricted':'R'}[case['target_classification']]
        if not case['target_doc_id'].startswith('DOC-'+prefix):
            raise ValueError(f'Target ID không khớp classification: {case["test_id"]}')
    normal = sum(c['category'] == 'normal_rbac' for c in cases)
    attack = sum(c['category'] == 'attack' for c in cases)
    if normal < 25 or attack < 15:
        raise ValueError(f'Chưa đủ bộ kiểm thử: normal={normal}, attack={attack}')
    return cases


def run_live(cases):
    # Không gọi main() vì đó là CLI; inject components một lần để test lặp lại.
    from src.main import initialize_system, execute_end_to_end_pipeline
    with contextlib.redirect_stdout(io.StringIO()):
        components = initialize_system()
    results = []
    for case in cases:
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                outcome = execute_end_to_end_pipeline(
                    case['query'], case['role'], components, test_id=case['test_id'])
            ids = outcome.get('retrieved_doc_ids', [])
            target_found = case['target_doc_id'] in ids
            expected_found = bool(case['expected_retrieval_success'])
            # PASS ở đây chỉ đo kiểm thử retrieval mục tiêu; không phải đánh giá toàn bộ câu trả lời.
            retrieval_pass = target_found == expected_found
            results.append({
                'test_id':case['test_id'], 'category':case['category'],
                'role':case['role'], 'target_doc_id':case['target_doc_id'],
                'expected_action':case['expected_action'],
                'target_retrieved':target_found, 'retrieval_pass':retrieval_pass,
                'status':outcome.get('status'), 'action_taken':outcome.get('action_taken'),
                'latency_ms':outcome.get('latency_ms'),
                # Không ghi raw answer hoặc raw query vào file kết quả.
                'output_review_required':True,
            })
        except Exception as ex:
            results.append({'test_id':case['test_id'], 'category':case['category'],
                            'retrieval_pass':False, 'status':'ERROR',
                            'error_type':type(ex).__name__,
                            'output_review_required':True})
    return results


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--validate-only', action='store_true', help='Kiểm tra cấu trúc 40 ca; không chạy hệ thống')
    group.add_argument('--live', action='store_true', help='Chạy pipeline thật; cần đủ modules và Ollama')
    args = parser.parse_args()
    cases = load_and_validate(QUERY_FILE)
    counts = Counter(c['category'] for c in cases)
    print(f'VALID: {len(cases)} cases; normal={counts["normal_rbac"]}, attack={counts["attack"]}')
    if args.validate_only:
        print('VALIDATION ONLY: không có kết quả hiệu năng/an toàn thực nghiệm.')
        return
    results = run_live(cases)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    dest = RESULT_DIR / 'test_results.json'
    dest.write_text(json.dumps({'generated_at':datetime.now(timezone.utc).isoformat(),
                                'mode':'LIVE', 'results':results}, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
    passed = sum(r['retrieval_pass'] for r in results)
    errors = sum(r['status']=='ERROR' for r in results)
    print(f'LIVE retrieval target checks: {passed}/{len(results)} passed; errors={errors}')
    print('Lưu ý: chưa đo độ đúng câu trả lời, leakage từ nội dung, false refusal hoặc groundedness.')
    print(f'Kết quả: {dest}')
    if errors:
        sys.exit(2)

if __name__ == '__main__':
    main()
