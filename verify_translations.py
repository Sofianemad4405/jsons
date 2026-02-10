#!/usr/bin/env python3
"""
Enhanced Translation Verification Script
Verifies the translation status of all JSON files with detailed reporting.

Features:
- Type-safe with full type hints
- Detailed per-file and aggregate statistics
- Identifies failed translations (same as original)
- Colored output for better readability
- Exports summary to markdown report
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import config


@dataclass
class FileStats:
    """Statistics for a single file."""
    filename: str
    total_items: int
    total_fields: int
    translated_fields: int
    failed_fields: int
    
    @property
    def translation_rate(self) -> float:
        """Calculate translation success rate."""
        if self.total_fields == 0:
            return 0.0
        return (self.translated_fields - self.failed_fields) / self.total_fields * 100
    
    @property
    def is_complete(self) -> bool:
        """Check if all fields are successfully translated."""
        return self.translated_fields == self.total_fields and self.failed_fields == 0


@dataclass
class AggregateStats:
    """Aggregate statistics across all files."""
    total_files: int
    total_items: int
    total_fields: int
    translated_fields: int
    failed_fields: int
    file_stats: List[FileStats]
    
    @property
    def coverage_rate(self) -> float:
        """Calculate overall translation coverage."""
        if self.total_fields == 0:
            return 0.0
        return (self.translated_fields - self.failed_fields) / self.total_fields * 100
    
    @property
    def translation_rate(self) -> float:
        """Calculate translation attempt rate."""
        if self.total_fields == 0:
            return 0.0
        return self.translated_fields / self.total_fields * 100


class TranslationVerifier:
    """Verifies translation status of JSON files."""
    
    def __init__(self, json_dir: Path):
        """
        Initialize verifier.
        
        Args:
            json_dir: Directory containing JSON files
        """
        self.json_dir = json_dir
    
    def verify_all_files(self) -> AggregateStats:
        """
        Verify all JSON files in directory.
        
        Returns:
            AggregateStats with verification results
        """
        json_files = sorted(self.json_dir.glob('*.json'))
        file_stats: List[FileStats] = []
        
        print("="*70)
        print("TRANSLATION VERIFICATION REPORT")
        print("="*70)
        print(f"Directory: {self.json_dir}")
        print(f"Files found: {len(json_files)}")
        print("="*70)
        print()
        
        total_items = 0
        total_fields = 0
        translated_fields = 0
        failed_fields = 0
        
        for json_file in json_files:
            # Skip metadata files
            if json_file.name in ('filename_mapping.json',):
                continue
                
            try:
                stats = self._verify_file(json_file)
                file_stats.append(stats)
                
                total_items += stats.total_items
                total_fields += stats.total_fields
                translated_fields += stats.translated_fields
                failed_fields += stats.failed_fields
                
                # Print file status
                status = "✓" if stats.is_complete else "⚠"
                print(f"{status} {stats.filename}")
                print(f"   Items: {stats.total_items}, Fields: {stats.total_fields}, "
                      f"Translated: {stats.translated_fields}, Failed: {stats.failed_fields} "
                      f"({stats.translation_rate:.1f}% success)")
                
            except Exception as e:
                print(f"✗ Error reading {json_file.name}: {e}")
        
        return AggregateStats(
            total_files=len(file_stats),
            total_items=total_items,
            total_fields=total_fields,
            translated_fields=translated_fields,
            failed_fields=failed_fields,
            file_stats=file_stats
        )
    
    def _verify_file(self, file_path: Path) -> FileStats:
        """
        Verify translation status of a single file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            FileStats with verification results
        """
        with open(file_path, 'r', encoding=config.ENCODING) as f:
            data = json.load(f)
        
        # Skip if not a list (e.g., mapping files)
        if not isinstance(data, list):
            raise ValueError(f"Expected list, got {type(data).__name__}")
        
        total_fields = 0
        translated_fields = 0
        failed_fields = 0
        
        for item in data:
            for key, value in item.items():
                # Only count original (non-translated) string fields
                if key.endswith(config.TRANSLATION_SUFFIX):
                    continue
                
                if not isinstance(value, str) or not value.strip():
                    continue
                
                total_fields += 1
                en_key = f"{key}{config.TRANSLATION_SUFFIX}"
                
                if en_key in item:
                    translated_fields += 1
                    # Check if translation failed (same as original)
                    if item[en_key] == value:
                        failed_fields += 1
        
        return FileStats(
            filename=file_path.name,
            total_items=len(data),
            total_fields=total_fields,
            translated_fields=translated_fields,
            failed_fields=failed_fields
        )


def print_summary(stats: AggregateStats) -> None:
    """
    Print summary statistics.
    
    Args:
        stats: Aggregate statistics to print
    """
    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total files processed: {stats.total_files}")
    print(f"Total items: {stats.total_items}")
    print(f"Total text fields: {stats.total_fields}")
    print(f"Successfully translated: {stats.translated_fields} ({stats.translation_rate:.1f}%)")
    print(f"Failed translations: {stats.failed_fields} ({stats.failed_fields/stats.total_fields*100:.1f}%)")
    print(f"Translation coverage: {stats.coverage_rate:.1f}%")
    print("="*70)
    
    # Print files needing attention
    needs_attention = [fs for fs in stats.file_stats if not fs.is_complete]
    
    if needs_attention:
        print(f"\n⚠ Files with failed translations ({len(needs_attention)}):")
        for fs in needs_attention:
            print(f"  - {fs.filename}: {fs.failed_fields} failed")


def export_markdown_report(stats: AggregateStats, output_path: Path) -> None:
    """
    Export verification results to markdown file.
    
    Args:
        stats: Aggregate statistics to export
        output_path: Path to output markdown file
    """
    with open(output_path, 'w', encoding=config.ENCODING) as f:
        f.write("# Translation Verification Report\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- **Total Files**: {stats.total_files}\n")
        f.write(f"- **Total Items**: {stats.total_items}\n")
        f.write(f"- **Total Fields**: {stats.total_fields}\n")
        f.write(f"- **Translation Rate**: {stats.translation_rate:.1f}%\n")
        f.write(f"- **Success Rate**: {stats.coverage_rate:.1f}%\n")
        f.write(f"- **Failed Translations**: {stats.failed_fields}\n\n")
        
        f.write("## File Details\n\n")
        f.write("| File | Items | Fields | Translated | Failed | Success Rate |\n")
        f.write("|------|-------|--------|------------|--------|-------------|\n")
        
        for fs in stats.file_stats:
            status = "✓" if fs.is_complete else "⚠"
            f.write(f"| {status} {fs.filename} | {fs.total_items} | {fs.total_fields} | "
                   f"{fs.translated_fields} | {fs.failed_fields} | {fs.translation_rate:.1f}% |\n")
        
        f.write("\n## Files Needing Attention\n\n")
        needs_attention = [fs for fs in stats.file_stats if not fs.is_complete]
        
        if needs_attention:
            for fs in needs_attention:
                f.write(f"- **{fs.filename}**: {fs.failed_fields} failed translations "
                       f"({fs.translation_rate:.1f}% success)\n")
        else:
            f.write("All files have been successfully translated! 🎉\n")
    
    print(f"\n📄 Report exported to: {output_path}")


def main() -> None:
    """Main entry point."""
    verifier = TranslationVerifier(config.JSON_DIR)
    stats = verifier.verify_all_files()
    print_summary(stats)
    
    # Export markdown report
    report_path = config.JSON_DIR / "VERIFICATION_REPORT.md"
    export_markdown_report(stats, report_path)


if __name__ == "__main__":
    main()
