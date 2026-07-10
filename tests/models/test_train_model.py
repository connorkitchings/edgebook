"""
Test cases for train_model.py
"""

from unittest.mock import patch

from vibe_coding.models.train_model import main


def test_train_model_main(caplog):
    with patch("vibe_coding.models.train_model.logger.info") as mock_logger_info:
        main()
        mock_logger_info.assert_any_call("Training model...")
        mock_logger_info.assert_any_call("Model trained successfully.")
