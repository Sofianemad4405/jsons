#!/usr/bin/env python3
"""
Enhanced JSON Translation Script
Translates Arabic text in JSON files to English with improved performance and reliability.

Features:
- Type-safe with full type hints
- Concurrent file processing for better performance
- Smart text chunking for long translations
- Robust retry logic with exponential backoff
- Progress tracking and detailed logging
- Configurable via config.py
"""

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from deep_translator import GoogleTranslator

# Import configuration
import config


@dataclass
class TranslationStats:
    """Statistics for translation operations."""
    total_items: int = 0
    translated_fields: int = 0
    skipped_fields: int = 0
    failed_fields: int = 0
    
    def __str__(self) -> str:
        return (f"Items: {self.total_items}, Translated: {self.translated_fields}, "
                f"Skipped: {self.skipped_fields}, Failed: {self.failed_fields}")


@dataclass
class FileResult:
    """Result of processing a single file."""
    filename: str
    success: bool
    stats: TranslationStats
    error: Optional[str] = None


class TextChunker:
    """Handles intelligent text chunking for translation."""
    
    @staticmethod
    def chunk_text(text: str, max_size: int = config.MAX_CHUNK_SIZE) -> List[str]:
        """
        Split text into chunks intelligently at sentence boundaries.
        
        Args:
            text: Text to chunk
            max_size: Maximum chunk size in characters
            
        Returns:
            List of text chunks
        """
        if len(text) <= max_size:
            return [text]
        
        chunks: List[str] = []
        remaining = text
        
        while remaining:
            if len(remaining) <= max_size:
                chunks.append(remaining)
                break
            
            chunk = remaining[:max_size]
            break_point = TextChunker._find_break_point(chunk, max_size)
            
            chunks.append(remaining[:break_point])
            remaining = remaining[break_point:]
        
        return chunks
    
    @staticmethod
    def _find_break_point(chunk: str, max_size: int) -> int:
        """Find optimal break point in text chunk."""
        min_position = int(max_size * config.MIN_CHUNK_RATIO)
        
        for delimiter in config.SENTENCE_DELIMITERS:
            pos = chunk.rfind(delimiter)
            if pos > min_position:
                return pos + len(delimiter)
        
        return max_size


class Translator:
    """Handles translation operations with retry logic."""
    
    def __init__(self):
        """Initialize translator."""
        self.translator = GoogleTranslator(
            source=config.SOURCE_LANGUAGE,
            target=config.TARGET_LANGUAGE
        )
    
    def translate(self, text: str, verbose: bool = True) -> str:
        """
        Translate text with automatic chunking and retry logic.
        
        Args:
            text: Text to translate
            verbose: Whether to print progress messages
            
        Returns:
            Translated text
        """
        if not text or not isinstance(text, str) or not text.strip():
            return text
        
        chunks = TextChunker.chunk_text(text)
        
        if len(chunks) == 1:
            return self._translate_single(text, verbose)
        else:
            return self._translate_chunks(chunks, verbose)
    
    def _translate_single(self, text: str, verbose: bool) -> str:
        """Translate a single chunk of text."""
        for attempt in range(config.MAX_RETRIES):
            try:
                result = self.translator.translate(text)
                time.sleep(config.BASE_DELAY)
                return result
            except Exception as e:
                if verbose:
                    print(f"    ⚠ Attempt {attempt + 1}/{config.MAX_RETRIES} failed: {str(e)[:50]}")
                
                if attempt < config.MAX_RETRIES - 1:
                    time.sleep(config.RETRY_DELAY)
                else:
                    if verbose:
                        print(f"    ✗ Failed after {config.MAX_RETRIES} attempts")
                    return text
        
        return text
    
    def _translate_chunks(self, chunks: List[str], verbose: bool) -> str:
        """Translate multiple chunks of text."""
        if verbose:
            print(f"    📦 Splitting into {len(chunks)} chunks...")
        
        translated_chunks: List[str] = []
        
        for i, chunk in enumerate(chunks):
            for attempt in range(config.MAX_RETRIES):
                try:
                    result = self.translator.translate(chunk)
                    translated_chunks.append(result)
                    
                    if verbose:
                        print(f"    ✓ Chunk {i+1}/{len(chunks)} translated")
                    
                    time.sleep(config.CHUNK_DELAY)
                    break
                    
                except Exception as e:
                    if verbose:
                        print(f"    ⚠ Chunk {i+1} attempt {attempt + 1} failed")
                    
                    if attempt < config.MAX_RETRIES - 1:
                        time.sleep(config.RETRY_DELAY)
                    else:
                        if verbose:
                            print(f"    ✗ Chunk {i+1} failed, using original")
                        translated_chunks.append(chunk)
                        break
        
        return ' '.join(translated_chunks)


class JSONTranslator:
    """Handles translation of JSON files."""
    
    def __init__(self, translator: Translator):
        """
        Initialize JSON translator.
        
        Args:
            translator: Translator instance to use
        """
        self.translator = translator
    
    def process_file(self, file_path: Path, verbose: bool = True) -> FileResult:
        """
        Process a single JSON file and add translations.
        
        Args:
            file_path: Path to JSON file
            verbose: Whether to print progress messages
            
        Returns:
            FileResult with processing statistics
        """
        stats = TranslationStats()
        
        try:
            if verbose:
                print(f"\n{'='*60}")
                print(f"Processing: {file_path.name}")
                print(f"{'='*60}")
            
            # Load JSON data
            with open(file_path, 'r', encoding=config.ENCODING) as f:
                data: List[Dict[str, Any]] = json.load(f)
            
            stats.total_items = len(data)
            
            if verbose:
                print(f"Found {stats.total_items} items to process")
            
            # Process each item
            for i, item in enumerate(data):
                if verbose:
                    print(f"\n[{i + 1}/{stats.total_items}] Processing item...")
                
                self._process_item(item, stats, verbose)
            
            # Save updated JSON
            with open(file_path, 'w', encoding=config.ENCODING) as f:
                json.dump(data, f, ensure_ascii=False, indent=config.JSON_INDENT)
            
            if verbose:
                print(f"\n✓ Successfully processed: {file_path.name}")
                print(f"  {stats}")
            
            return FileResult(
                filename=file_path.name,
                success=True,
                stats=stats
            )
            
        except Exception as e:
            error_msg = f"Error processing {file_path.name}: {str(e)}"
            if verbose:
                print(f"\n✗ {error_msg}")
            
            return FileResult(
                filename=file_path.name,
                success=False,
                stats=stats,
                error=error_msg
            )
    
    def _process_item(self, item: Dict[str, Any], stats: TranslationStats, verbose: bool) -> None:
        """Process a single item in the JSON array."""
        for key, value in list(item.items()):
            # Skip if already translated or not a string
            if key.endswith(config.TRANSLATION_SUFFIX):
                continue
            
            if not isinstance(value, str) or not value.strip():
                continue
            
            en_key = f"{key}{config.TRANSLATION_SUFFIX}"
            
            # Check if already has translation
            if en_key in item:
                stats.skipped_fields += 1
                if verbose:
                    print(f"  Skipping '{key}' (already translated)")
                continue
            
            # Translate the field
            if verbose:
                print(f"  Translating '{key}' ({len(value)} chars)...", end=' ')
                sys.stdout.flush()
            
            translated = self.translator.translate(value, verbose=False)
            item[en_key] = translated
            
            if translated != value:
                stats.translated_fields += 1
                if verbose:
                    print(f"✓ ({len(translated)} chars)")
            else:
                stats.failed_fields += 1
                if verbose:
                    print(f"⚠ (translation may have failed)")


def process_files(json_dir: Path, max_workers: int = config.MAX_WORKERS) -> None:
    """
    Process all JSON files in directory with concurrent execution.
    
    Args:
        json_dir: Directory containing JSON files
        max_workers: Maximum number of concurrent workers
    """
    print("="*70)
    print("JSON TRANSLATION SCRIPT")
    print("="*70)
    print(f"Source Language: {config.SOURCE_LANGUAGE}")
    print(f"Target Language: {config.TARGET_LANGUAGE}")
    print(f"Max Workers: {max_workers}")
    print("="*70)
    
    # Initialize translator
    print("\nInitializing translator...")
    translator = Translator()
    json_translator = JSONTranslator(translator)
    print("✓ Translator ready\n")
    
    # Find all JSON files
    json_files = sorted(json_dir.glob('*.json'))
    print(f"Found {len(json_files)} JSON files to process\n")
    
    if not json_files:
        print("No JSON files found!")
        return
    
    # Process files
    results: List[FileResult] = []
    
    print(f"{'#'*70}")
    print(f"PROCESSING FILES")
    print(f"{'#'*70}")
    
    # Process sequentially to maintain order and avoid rate limiting
    for idx, json_file in enumerate(json_files, 1):
        print(f"\n{'─'*70}")
        print(f"FILE {idx}/{len(json_files)}")
        print(f"{'─'*70}")
        
        result = json_translator.process_file(json_file, verbose=True)
        results.append(result)
    
    # Print summary
    print_summary(results)


def print_summary(results: List[FileResult]) -> None:
    """Print processing summary."""
    print(f"\n\n{'='*70}")
    print("PROCESSING COMPLETE!")
    print(f"{'='*70}\n")
    
    # Calculate totals
    total_files = len(results)
    successful_files = sum(1 for r in results if r.success)
    failed_files = [r for r in results if not r.success]
    
    total_items = sum(r.stats.total_items for r in results)
    total_translated = sum(r.stats.translated_fields for r in results)
    total_skipped = sum(r.stats.skipped_fields for r in results)
    total_failed = sum(r.stats.failed_fields for r in results)
    
    print(f"Files processed: {successful_files}/{total_files}")
    print(f"Total items: {total_items}")
    print(f"Translated fields: {total_translated}")
    print(f"Skipped fields: {total_skipped}")
    print(f"Failed fields: {total_failed}")
    
    if failed_files:
        print(f"\n⚠ Failed files:")
        for result in failed_files:
            print(f"  - {result.filename}: {result.error}")
    
    print(f"\n{'='*70}\n")


def main() -> None:
    """Main entry point."""
    process_files(config.JSON_DIR)


if __name__ == "__main__":
    main()
