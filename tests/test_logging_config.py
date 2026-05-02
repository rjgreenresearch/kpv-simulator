"""
tests/test_logging_config.py
=============================
Tests for kpvs.logging_config — level validation, handler setup,
file creation, quiet mode.
"""

import logging
import os
import tempfile
import pytest
from kpvs.logging_config import configure_logging, get_run_logger


class TestConfigureLogging:

    def teardown_method(self):
        """Clean up root logger handlers after each test."""
        root = logging.getLogger()
        root.handlers.clear()

    def test_invalid_level_raises(self):
        with pytest.raises(ValueError, match="Invalid"):
            configure_logging(level="VERBOSE")

    def test_valid_levels_accepted(self):
        for lvl in ("DEBUG","INFO","WARNING","ERROR","CRITICAL"):
            configure_logging(level=lvl, log_file="", quiet=True)
            assert logging.getLogger().level == getattr(logging, lvl)

    def test_quiet_suppresses_console(self):
        configure_logging(level="INFO", log_file="", quiet=True)
        root = logging.getLogger()
        stream_handlers = [h for h in root.handlers
                           if isinstance(h, logging.StreamHandler)
                           and not isinstance(h, logging.FileHandler)]
        assert len(stream_handlers) == 0

    def test_console_handler_added(self):
        configure_logging(level="INFO", log_file="", quiet=False)
        root = logging.getLogger()
        stream_handlers = [h for h in root.handlers
                           if isinstance(h, logging.StreamHandler)
                           and not isinstance(h, logging.FileHandler)]
        assert len(stream_handlers) >= 1

    def test_file_logging_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            configure_logging(level="INFO", log_file=log_path, quiet=True)
            logging.getLogger("kpvs").info("test message")
            assert os.path.exists(log_path)
            with open(log_path) as f:
                content = f.read()
            assert "test message" in content

    def test_empty_string_suppresses_file(self):
        configure_logging(level="INFO", log_file="", quiet=True)
        root = logging.getLogger()
        file_handlers = [h for h in root.handlers
                         if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 0

    def test_no_log_file_auto_creates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            configure_logging(level="INFO", log_file=None,
                              log_dir=tmpdir, quiet=True)
            root = logging.getLogger()
            file_handlers = [h for h in root.handlers
                             if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) >= 1

    def test_duplicate_handlers_cleared_on_reconfigure(self):
        configure_logging(level="INFO", log_file="", quiet=True)
        configure_logging(level="INFO", log_file="", quiet=True)
        root = logging.getLogger()
        # Should not accumulate handlers across calls
        assert len(root.handlers) <= 2


class TestGetRunLogger:

    def test_returns_logger(self):
        logger = get_run_logger("test_run")
        assert isinstance(logger, logging.Logger)

    def test_name_contains_run_id(self):
        logger = get_run_logger("run_abc123")
        assert "run_abc123" in logger.name

    def test_different_ids_different_loggers(self):
        l1 = get_run_logger("run_001")
        l2 = get_run_logger("run_002")
        assert l1 is not l2
