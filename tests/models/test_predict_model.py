"""
Test cases for predict_model.py
"""

from unittest.mock import patch

from vibe_coding.models.predict_model import main


def test_predict_model_main(caplog):
    with patch("vibe_coding.models.predict_model.logger.info") as mock_logger_info:
        main()
        mock_logger_info.assert_any_call("Making predictions...")
        mock_logger_info.assert_any_call("Predictions made successfully.")
