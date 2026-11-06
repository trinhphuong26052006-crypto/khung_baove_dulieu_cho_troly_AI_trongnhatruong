"""Chạy ở project root: python cleanup_logs.py [--apply]"""
import argparse
from pathlib import Path
from src.logging.security_logger import SecurityLogger

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--apply', action='store_true', help='Thực sự xóa log hết hạn; mặc định chỉ xem trước')
    p.add_argument('--days', type=int, default=30)
    args = p.parse_args()
    log_path = Path(__file__).resolve().parent / 'data/logs/security_audit.log'
    logger = SecurityLogger(log_path, retention_days=args.days)
    report = logger.cleanup_expired(dry_run=not args.apply)
    print('APPLY' if args.apply else 'DRY RUN', report)
