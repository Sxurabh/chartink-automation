# app/utils/logger.py
import logging
import sys
import io
import re

EMOJI_PATTERN = re.compile(r'[\U0001F300-\U0001F9FF\u2600-\u27BF\u2300-\u23FF\uFE0F]')

def _strip_emojis(msg):
    return EMOJI_PATTERN.sub('', str(msg)).strip()

class EmojiSafeStreamHandler(logging.StreamHandler):
    def emit(self, record):
        record.msg = _strip_emojis(record.msg)
        if record.args:
            record.args = tuple(_strip_emojis(a) if isinstance(a, str) else a for a in record.args)
        super().emit(record)

def setup_logger():
    logger = logging.getLogger("ChartInkAutomation")
    logger.setLevel(logging.INFO)

    handler = EmojiSafeStreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger

# Create a singleton logger instance
log = setup_logger()