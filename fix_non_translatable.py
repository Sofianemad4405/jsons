#!/usr/bin/env python3
"""
Fix Non-Translatable Fields Script
Handles special cases where fields don't need translation (e.g., booleans, numbers).

This script identifies and fixes fields that contain values that shouldn't be
translated but were marked as "failed" translations.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import config


class NonTranslatableFixer:
    """Fixes fields that don't need translation."""
    
    # Values that don't need translation
    NON_TRANSLATABLE_VALUES: Set[str] = {
        'true', 'false', 'null', 'yes', 'no',
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'
    }
    
    def __init__(self, json_dir: Path):
        """
        Initialize fixer.
        
        Args:
            json_dir: Directory containing JSON files
        """
        self.json_dir = json_dir
        self.total_fixed = 0
        self.files_modified = 0
    
    def fix_all_files(self) -> None:
        """Fix all JSON files in directory."""
        json_files = sorted(self.json_dir.glob('*.json'))
        
        # Skip metadata files
        json_files = [f for f in json_files if f.name not in ('filename_mapping.json',)]
        
        print("="*70)
        print("FIXING NON-TRANSLATABLE FIELDS")
        print("="*70)
        print(f"Files to check: {len(json_files)}")
        print("="*70)
        print()
        
        for json_file in json_files:
            try:
                if self._fix_file(json_file):
                    self.files_modified += 1
            except Exception as e:
                print(f"✗ Error processing {json_file.name}: {e}")
        
        print()
        print("="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Files modified: {self.files_modified}")
        print(f"Fields fixed: {self.total_fixed}")
        print("="*70)
    
    def _fix_file(self, file_path: Path) -> bool:
        """
        Fix non-translatable fields in a single file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            True if file was modified, False otherwise
        """
        with open(file_path, 'r', encoding=config.ENCODING) as f:
            data: List[Dict[str, Any]] = json.load(f)
        
        # Skip if not a list
        if not isinstance(data, list):
            return False
        
        modified = False
        fixed_count = 0
        
        for item in data:
            for key, value in list(item.items()):
                # Skip if already translated
                if key.endswith(config.TRANSLATION_SUFFIX):
                    continue
                
                if not isinstance(value, str):
                    continue
                
                en_key = f"{key}{config.TRANSLATION_SUFFIX}"
                
                # Check if this is a non-translatable value
                if value.lower().strip() in self.NON_TRANSLATABLE_VALUES:
                    # If translation exists and is different, fix it
                    if en_key in item and item[en_key] != value:
                        item[en_key] = value
                        modified = True
                        fixed_count += 1
                    # If translation doesn't exist, add it
                    elif en_key not in item:
                        item[en_key] = value
                        modified = True
                        fixed_count += 1
        
        if modified:
            with open(file_path, 'w', encoding=config.ENCODING) as f:
                json.dump(data, f, ensure_ascii=False, indent=config.JSON_INDENT)
            
            print(f"✓ Fixed {file_path.name}: {fixed_count} fields")
            self.total_fixed += fixed_count
        
        return modified


def main() -> None:
    """Main entry point."""
    fixer = NonTranslatableFixer(config.JSON_DIR)
    fixer.fix_all_files()
    
    print("\n💡 Tip: Run verify_translations.py to see updated statistics")


if __name__ == "__main__":
    main()
