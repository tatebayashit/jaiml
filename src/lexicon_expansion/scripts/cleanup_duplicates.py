#!/usr/bin/env python3
"""
辞書拡張システムの不要ファイル・重複定義を整理するスクリプト
"""
import sys
from pathlib import Path
import shutil
from typing import List, Set

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

def find_duplicate_files(root_dir: Path) -> List[Path]:
    """重複・不要ファイルの検出"""
    duplicates = []
    
    # 重複requirements.txt
    requirements_files = list(root_dir.rglob("requirements.txt"))
    if len(requirements_files) > 1:
        # メインのrequirements.txt以外を重複とみなす
        main_req = root_dir.parent.parent / "model" / "jaiml_v3_3" / "requirements.txt"
        for req_file in requirements_files:
            if req_file != main_req:
                duplicates.append(req_file)
    
    # 一時ファイル
    temp_patterns = ["*.pyc", "__pycache__", "*.tmp", "*.bak", ".DS_Store"]
    for pattern in temp_patterns:
        duplicates.extend(root_dir.rglob(pattern))
    
    # 空のディレクトリ
    for dir_path in root_dir.rglob("*"):
        if dir_path.is_dir() and not any(dir_path.iterdir()):
            duplicates.append(dir_path)
            
    return duplicates

def check_unused_imports(root_dir: Path) -> List[str]:
    """未使用インポートの検出"""
    issues = []
    
    # Python ファイルを検査
    for py_file in root_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
            
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # fugashiのインポートをチェック（lexical.pyで未使用）
        if "import fugashi" in content and py_file.name == "lexical.py":
            if "fugashi." not in content and "_tagger = fugashi" not in content:
                issues.append(f"{py_file}: 未使用のfugashiインポート")
                
    return issues

def cleanup_lexicon_expansion(dry_run: bool = True):
    """辞書拡張システムのクリーンアップ"""
    expansion_root = Path(__file__).resolve().parent.parent
    
    print("辞書拡張システムのクリーンアップを開始します...")
    print(f"対象ディレクトリ: {expansion_root}")
    
    if dry_run:
        print("\n[DRY RUN モード - 実際の削除は行いません]")
    
    # 1. 重複ファイルの検出
    duplicates = find_duplicate_files(expansion_root)
    
    if duplicates:
        print("\n## 削除対象ファイル:")
        for dup in sorted(duplicates):
            print(f"  - {dup.relative_to(expansion_root)}")
            if not dry_run:
                if dup.is_dir():
                    shutil.rmtree(dup)
                else:
                    dup.unlink()
    else:
        print("\n重複ファイルは見つかりませんでした。")
    
    # 2. 未使用インポートの検出
    import_issues = check_unused_imports(expansion_root)
    
    if import_issues:
        print("\n## 未使用インポート:")
        for issue in import_issues:
            print(f"  - {issue}")
    
    # 3. 推奨ディレクトリ構造の確認
    expected_dirs = [
        "config",
        "scripts", 
        "corpus",
        "outputs",
        "annotation",
        "clustering",
        "version_control"
        "candidates"
    ]
    
    missing_dirs = []
    for dir_name in expected_dirs:
        dir_path = expansion_root / dir_name
        if not dir_path.exists():
            missing_dirs.append(dir_name)
            if not dry_run:
                dir_path.mkdir(parents=True, exist_ok=True)
    
    if missing_dirs:
        print("\n## 作成された必須ディレクトリ:")
        for dir_name in missing_dirs:
            print(f"  - {dir_name}/")
    
    # 4. サマリー
    print("\n## クリーンアップサマリー:")
    print(f"  削除対象ファイル数: {len(duplicates)}")
    print(f"  未使用インポート: {len(import_issues)}")
    print(f"  作成ディレクトリ数: {len(missing_dirs)}")
    
    if dry_run:
        print("\n実際にクリーンアップを実行するには、--execute オプションを付けて実行してください。")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="辞書拡張システムの不要ファイル整理"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="実際にファイルの削除・整理を実行する"
    )
    
    args = parser.parse_args()
    
    cleanup_lexicon_expansion(dry_run=not args.execute)

if __name__ == "__main__":
    main()