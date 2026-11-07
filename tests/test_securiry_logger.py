import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from src.logging.security_logger import SecurityLogger

class TestSecurityLogger(unittest.TestCase):
    def test_minimization_and_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'audit.jsonl'
            logger = SecurityLogger(path, retention_days=30)
            secret = 'Mã giả lập nhạy cảm TEST-SECRET-123'
            logger.log_event(role='SinhVien', query=secret, status='DENIED')
            self.assertNotIn(secret, path.read_text(encoding='utf-8'))
            old = {'timestamp': (datetime.now(timezone.utc) - timedelta(days=40)).isoformat(), 'status': 'OLD'}
            with path.open('a', encoding='utf-8') as f:
                f.write(json.dumps(old) + '\n')
            self.assertEqual(logger.cleanup_expired(dry_run=True)['expired'], 1)
            self.assertEqual(len(path.read_text(encoding='utf-8').splitlines()), 2)
            self.assertEqual(logger.cleanup_expired(dry_run=False)['expired'], 1)
            self.assertEqual(len(path.read_text(encoding='utf-8').splitlines()), 1)

if __name__ == '__main__':
    unittest.main()
