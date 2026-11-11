
"""Dọn log hết hạn. Chạy từ thư mục gốc dự án."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.logging.security_logger import SecurityLogger


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Thực sự xóa log hết hạn; mặc định chỉ xem trước"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Thời hạn lưu log (ngày)"
    )

    args = parser.parse_args()

    if args.days <= 0:
        parser.error("--days phải lớn hơn 0")

    log_path = ROOT / "logs" / "security_audit.jsonl"

    logger = SecurityLogger(
        log_path,
        retention_days=args.days
    )

    report = logger.cleanup_expired(
        dry_run=not args.apply
    )

    print("APPLY" if args.apply else "DRY RUN")
    print(report)


if __name__ == "__main__":
    main()
