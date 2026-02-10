#!/usr/bin/env python3
"""
JSON File Numbering Script
Renames JSON files by adding sequential numbers as prefixes.

Features:
- Adds sequential numbers (01, 02, etc.) to filenames
- Preserves Arabic characters in filenames
- Creates backup before renaming
- Generates mapping file for reference
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

import config


class FileNumberer:
    """Handles numbering of JSON files."""
    
    def __init__(self, json_dir: Path):
        """
        Initialize file numberer.
        
        Args:
            json_dir: Directory containing JSON files
        """
        self.json_dir = json_dir
    
    def number_files(self, create_backup: bool = True) -> Dict[str, str]:
        """
        Add sequential numbers to JSON filenames.
        
        Args:
            create_backup: Whether to create backup before renaming
            
        Returns:
            Dictionary mapping old names to new names
        """
        # Get all JSON files (excluding backup files)
        json_files = sorted([
            f for f in self.json_dir.glob('*.json')
            if not f.name.endswith('.backup')
        ])
        
        if not json_files:
            print("No JSON files found!")
            return {}
        
        print("="*70)
        print("JSON FILE NUMBERING SCRIPT")
        print("="*70)
        print(f"Directory: {self.json_dir}")
        print(f"Files found: {len(json_files)}")
        print("="*70)
        print()
        
        # Create mapping of old to new names
        mapping: Dict[str, str] = {}
        total_digits = len(str(len(json_files)))
        
        for idx, file_path in enumerate(json_files, 1):
            old_name = file_path.name
            number_prefix = str(idx).zfill(total_digits)
            new_name = f"{number_prefix}_{old_name}"
            mapping[old_name] = new_name
        
        # Show what will be renamed
        print("Planned renames:")
        print("-" * 70)
        for old_name, new_name in mapping.items():
            print(f"  {old_name}")
            print(f"  → {new_name}")
            print()
        
        # Create backup if requested
        if create_backup:
            print("\n📦 Creating backup...")
            backup_dir = self.json_dir / "backup_before_numbering"
            backup_dir.mkdir(exist_ok=True)
            
            for file_path in json_files:
                shutil.copy2(file_path, backup_dir / file_path.name)
            
            print(f"✓ Backup created at: {backup_dir}")
        
        # Perform renaming
        print("\n🔄 Renaming files...")
        for old_path in json_files:
            old_name = old_path.name
            new_name = mapping[old_name]
            new_path = old_path.parent / new_name
            
            old_path.rename(new_path)
            print(f"  ✓ Renamed: {old_name}")
        
        # Save mapping to file
        mapping_path = self.json_dir / "filename_mapping.json"
        with open(mapping_path, 'w', encoding=config.ENCODING) as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Mapping saved to: {mapping_path}")
        
        return mapping


def print_summary(mapping: Dict[str, str]) -> None:
    """
    Print numbering summary.
    
    Args:
        mapping: Dictionary of old to new filenames
    """
    print()
    print("="*70)
    print("NUMBERING COMPLETE!")
    print("="*70)
    print(f"Total files renamed: {len(mapping)}")
    print("="*70)


def main() -> None:
    """Main entry point."""
    numberer = FileNumberer(config.JSON_DIR)
    mapping = numberer.number_files(create_backup=True)
    print_summary(mapping)


if __name__ == "__main__":
    main()
