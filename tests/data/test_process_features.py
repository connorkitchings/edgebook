"""
Test cases for process_features.py
"""

from unittest.mock import patch

from vibe_coding.data.process_features import main


def test_process_features_main(caplog):
    with patch("vibe_coding.data.process_features.logger.info") as mock_logger_info:
        main()
        mock_logger_info.assert_any_call("Processing features...")
        mock_logger_info.assert_any_call("Features processed successfully.")
