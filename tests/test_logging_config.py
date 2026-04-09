"""Tests for application logging configuration."""

from __future__ import annotations

import logging
import os
import tempfile
import unittest
from pathlib import Path

from nfs_scanner.infra.logging_config import LOG_DIRECTORY_ENV_VAR, setup_logging


class LoggingConfigTestCase(unittest.TestCase):
    """Verify logging bootstrap behavior for persistent daily logs."""

    def test_setup_logging_writes_to_daily_log_file(self) -> None:
        """setup_logging should create a date-based log file and write log entries."""

        with tempfile.TemporaryDirectory() as temp_dir:
            log_root = Path(temp_dir)
            previous_value = os.environ.get(LOG_DIRECTORY_ENV_VAR)
            os.environ[LOG_DIRECTORY_ENV_VAR] = str(log_root)

            try:
                log_file = setup_logging(force=True)
                logger = logging.getLogger("tests.logging")
                message = "日志系统可按天落盘"
                logger.info(message)

                self.assertTrue(log_file.exists())
                self.assertEqual(log_file.parent, log_root)
                self.assertRegex(log_file.name, r"^\d{4}-\d{2}-\d{2}\.log$")
                self.assertIn(message, log_file.read_text(encoding="utf-8"))
            finally:
                if previous_value is None:
                    os.environ.pop(LOG_DIRECTORY_ENV_VAR, None)
                else:
                    os.environ[LOG_DIRECTORY_ENV_VAR] = previous_value


if __name__ == "__main__":
    unittest.main()
