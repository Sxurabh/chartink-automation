# app/utils/logger.py
import logging
import sys

def setup_logger():
    """
    Configures and returns a logger instance.
    """
    logger = logging.getLogger("ChartInkAutomation")
    logger.setLevel(logging.INFO)

    # Create a handler to print logs to the console
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    # Add the handler to the logger
    if not logger.handlers:
        logger.addHandler(handler)

    return logger

# Create a singleton logger instance
log = setup_logger()