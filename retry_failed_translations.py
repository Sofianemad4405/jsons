#!/usr/bin/env python3
"""
Enhanced Translation Retry Script
Retries only fields where translation failed (English text equals Arabic text).

Features:
- Type-safe with full type hints
- Targets only failed translations
- Detailed progress tracking
- Configurable retry logic
- Summary reporting
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any

import config
from translate_json import Translator


@dataclass
class RetryStats:
    """Statistics for retry operations."""
    files_processed: int = 0
    fields_retried: int = 0
    fields_fixed: int = 0
    fields_still_failed: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate retry success rate."""
        if self.fields_retried == 0:
            return 0.0
        return self.fields_fixed / self.fields_retried * 100


@dataclass
class FileRetryResult:
    """Result of retrying translations in a file."""
    filename: str
    fields_retried: int
    fields_fixed: int
    modified: bool


class TranslationRetrier:
    """Handles retrying failed translations."""
    
    def __init__(self, json_dir: Path, translator: Translator):
        """
        Initialize retrier.
        
        Args:
            json_dir: Directory containing JSON files
            translator: Translator instance to use
        """
        self.json_dir = json_dir
        self.translator = translator
    
    def retry_all_files(self) -> RetryStats:
        """
        Retry failed translations in all JSON files.
        
        Returns:
            RetryStats with retry results
        """
        json_files = sorted(self.json_dir.glob('*.json'))
        stats = RetryStats()
        
        print("="*70)
        print("RETRYING FAILED TRANSLATIONS")
        print("="*70)
        print(f"Directory: {self.json_dir}")
        print(f"Files to check: {len(json_files)}")
        print("="*70)
        print()
        
        for json_file in json_files:
            try:
                result = self._retry_file(json_file)
                
                if result.fields_retried > 0:
                    stats.files_processed += 1
                    stats.fields_retried += result.fields_retried
                    stats.fields_fixed += result.fields_fixed
                    stats.fields_still_failed += (result.fields_retried - result.fields_fixed)
                    
                    status = "✓" if result.fields_fixed == result.fields_retried else "⚠"
                    print(f"\n{status} {result.filename}")
                    print(f"   Retried: {result.fields_retried}, "
                          f"Fixed: {result.fields_fixed}, "
                          f"Still failed: {result.fields_retried - result.fields_fixed}")
                    
                    if result.modified:
                        print(f"   💾 File updated")
                        
            except Exception as e:
                print(f"\n✗ Error processing {json_file.name}: {e}")
        
        return stats
    
    def _retry_file(self, file_path: Path) -> FileRetryResult:
        """
        Retry failed translations in a single file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            FileRetryResult with retry results
        """
        with open(file_path, 'r', encoding=config.ENCODING) as f:
            data: List[Dict[str, Any]] = json.load(f)
        
        fields_retried = 0
        fields_fixed = 0
        modified = False
        
        for i, item in enumerate(data):
            for key, value in list(item.items()):
                # Skip if already translated or not a string
                if key.endswith(config.TRANSLATION_SUFFIX):
                    continue
                
                if not isinstance(value, str) or not value.strip():
                    continue
                
                en_key = f"{key}{config.TRANSLATION_SUFFIX}"
                
                # Check if translation exists and failed (same as original)
                if en_key in item and item[en_key] == value:
                    print(f"\n  📝 {file_path.name} - Item {i+1} - Field '{key}'")
                    print(f"     Length: {len(value)} chars")
                    
                    fields_retried += 1
                    
                    # Retry translation
                    translated = self.translator.translate(value, verbose=False)
                    
                    # Check if translation succeeded (different from original)
                    if translated != value:
                        item[en_key] = translated
                        modified = True
                        fields_fixed += 1
                        print(f"     ✓ Translation successful!")
                    else:
                        print(f"     ✗ Translation still failed")
        
        # Save file if modifications were made
        if modified:
            with open(file_path, 'w', encoding=config.ENCODING) as f:
                json.dump(data, f, ensure_ascii=False, indent=config.JSON_INDENT)
        
        return FileRetryResult(
            filename=file_path.name,
            fields_retried=fields_retried,
            fields_fixed=fields_fixed,
            modified=modified
        )


def print_summary(stats: RetryStats) -> None:
    """
    Print retry summary.
    
    Args:
        stats: Retry statistics to print
    """
    print()
    print("="*70)
    print("RETRY SUMMARY")
    print("="*70)
    print(f"Files with failed translations: {stats.files_processed}")
    print(f"Total fields retried: {stats.fields_retried}")
    print(f"Successfully fixed: {stats.fields_fixed} ({stats.success_rate:.1f}%)")
    print(f"Still failed: {stats.fields_still_failed}")
    print("="*70)
    
    if stats.fields_still_failed > 0:
        print(f"\n⚠ {stats.fields_still_failed} translations still need attention")
        print("  Consider:")
        print("  - Using a different translation service")
        print("  - Manual translation for very long texts")
        print("  - Breaking down very long texts into smaller parts")


def main() -> None:
    """Main entry point."""
    print("Initializing translator...")
    translator = Translator()
    print("✓ Translator ready\n")
    
    retrier = TranslationRetrier(config.JSON_DIR, translator)
    stats = retrier.retry_all_files()
    print_summary(stats)


if __name__ == "__main__":
    main()
