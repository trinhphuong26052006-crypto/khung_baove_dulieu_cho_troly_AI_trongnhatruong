"""Nhật ký kiểm toán tối thiểu và dọn dẹp theo hạn lưu trữ.

Dùng JSON Lines; không ghi prompt, câu trả lời hay nội dung tài liệu.
Đây là bản prototype: phân quyền file/đồng bộ ghi cần cấu hình bổ sung khi triển khai thật.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

VALID_ROLES = {'SinhVien', 'GiangVien', 'QuanTri'}


class SecurityLogger:
    def __init__(self, log_path: str | Path, retention_days: int = 30, enabled: bool = True):
        if retention_days < 1:
            raise ValueError('retention_days phải >= 1')
        self.path = Path(log_path)
        self.retention_days = retention_days
        self.enabled = enabled
        if enabled:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, *, role: str, query: str, status: str,
                  retrieved_doc_ids: Optional[list[str]] = None,
                  action_taken: str = 'NOT_RUN', violation_count: int = 0,
                  latency_ms: Optional[float] = None, test_id: Optional[str] = None) -> dict[str, Any]:
        """Ghi dữ liệu tối thiểu; từ chối log nếu không ghi được (không im lặng)."""
        if role not in VALID_ROLES:
            role = 'UNKNOWN'
        event = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'role': role,
            'query_sha256': hashlib.sha256(query.encode('utf-8')).hexdigest(),
            'query_length': len(query),
            'status': str(status)[:80],
            'retrieved_doc_ids': [str(x) for x in (retrieved_doc_ids or []) if x][:20],
            'action_taken': str(action_taken)[:32],
            'violation_count': int(violation_count),
            'latency_ms': round(float(latency_ms), 2) if latency_ms is not None else None,
            'test_id': test_id,
        }
        if self.enabled:
            with self.path.open('a', encoding='utf-8') as f:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
        return event

    def cleanup_expired(self, *, now: Optional[datetime] = None, dry_run: bool = True) -> dict[str, int]:
        """Xóa dòng hết hạn theo timestamp UTC; giữ dòng lỗi để kiểm tra thủ công.

        dry_run=True mặc định để tránh xóa ngoài ý muốn.
        Chỉ thao tác trên file audit được cấu hình, không xóa tài liệu nguồn.
        """
        if not self.path.exists():
            return {'total': 0, 'expired': 0, 'invalid': 0, 'retained': 0}
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            raise ValueError('now phải có timezone')
        cutoff = now.astimezone(timezone.utc) - timedelta(days=self.retention_days)
        retained, expired, invalid = [], 0, 0
        with self.path.open('r', encoding='utf-8') as f:
            for line in f:
                try:
                    event = json.loads(line)
                    dt = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                    if dt.tzinfo is None:
                        raise ValueError('timestamp thiếu timezone')
                    if dt.astimezone(timezone.utc) < cutoff:
                        expired += 1
                        continue
                except (ValueError, KeyError, TypeError, json.JSONDecodeError):
                    invalid += 1
                retained.append(line)
        if not dry_run and expired:
            fd, tmp = tempfile.mkstemp(prefix='.audit-', suffix='.tmp', dir=self.path.parent)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    f.writelines(retained)
                os.replace(tmp, self.path)
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)
        return {'total': len(retained) + expired, 'expired': expired,
                'invalid': invalid, 'retained': len(retained)}