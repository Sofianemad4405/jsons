#!/usr/bin/env python3
"""
Configuration file for JSON translation scripts.
Centralizes all settings for easy maintenance and modification.
"""

from pathlib import Path
from typing import Final

# Directory Configuration
JSON_DIR: Final[Path] = Path(__file__).parent
OUTPUT_DIR: Final[Path] = JSON_DIR

# Translation Configuration
SOURCE_LANGUAGE: Final[str] = 'ar'  # Arabic
TARGET_LANGUAGE: Final[str] = 'en'  # English
TRANSLATION_SUFFIX: Final[str] = '-en'

# Performance Configuration
MAX_CHUNK_SIZE: Final[int] = 500  # Maximum characters per translation chunk
MAX_RETRIES: Final[int] = 5  # Maximum retry attempts for failed translations
BASE_DELAY: Final[float] = 0.5  # Base delay between translations (seconds)
CHUNK_DELAY: Final[float] = 1.0  # Delay between chunks (seconds)
RETRY_DELAY: Final[float] = 3.0  # Delay between retries (seconds)
MAX_WORKERS: Final[int] = 3  # Number of concurrent file processors

# Chunk Detection
MIN_CHUNK_RATIO: Final[float] = 0.5  # Minimum ratio for finding break points
SENTENCE_DELIMITERS: Final[tuple] = ('. ', '.\n', '؟ ', '! ', '، ', '\n\n', '\n')

# Output Configuration
JSON_INDENT: Final[int] = 2  # JSON file indentation
ENCODING: Final[str] = 'utf-8'  # File encoding
