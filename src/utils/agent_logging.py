"""
Structured Logging for Vibe Coding
==================================
This module provides a logger that outputs structured logs (Key=Value or JSON)
optimized for AI Agents to parse.

Usage:
    from src.utils.agent_logging import agent_logger

    agent_logger.info("Ingestion started", step="INGEST", source="Nugs")
    # Output: [INFO] [STEP:INGEST] Ingestion started source=Nugs
"""

import logging
import sys


class AgentFormatter(logging.Formatter):
    """
    Formats logs in a way that is easy for LLMs to parse using regex or simple
    splitting.
    Format: [LEVEL] [STEP:StepName] Message key=value
    """

    def format(self, record):
        msg = record.getMessage()

        # Extract 'step' from extra fields if present
        step = getattr(record, "step", "GENERAL")

        # Format basics
        prefix = f"[{record.levelname}] [STEP:{step}]"

        # Extract other extras
        extras = []
        for key, value in record.__dict__.items():
            if key not in [
                "step",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "name",
            ]:
                extras.append(f"{key}={value}")

        extra_str = " " + " ".join(extras) if extras else ""

        return f"{prefix} {msg}{extra_str}"


def setup_logger(name="vibe-agent"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Console Handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(AgentFormatter())

    if not logger.handlers:
        logger.addHandler(handler)

    return logger


agent_logger = setup_logger()

if __name__ == "__main__":
    # Demo
    agent_logger.info("System initialized")
    agent_logger.info("Processing file", step="PARSING", file="data.csv", size="10MB")
    agent_logger.warning("Rate limit approaching", step="API", limit=100, remaining=5)
