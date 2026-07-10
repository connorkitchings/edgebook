"""
Test cases for training_pipeline.py
"""

from unittest.mock import patch

from vibe_coding.pipelines.training_pipeline import main


def test_training_pipeline_main(caplog):
    with patch(
        "vibe_coding.pipelines.training_pipeline.logger.info"
    ) as mock_logger_info:
        main()
        mock_logger_info.assert_any_call("Running training pipeline...")
        mock_logger_info.assert_any_call("Training pipeline completed successfully.")
