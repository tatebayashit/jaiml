import argparse
import sys
from pathlib import Path
import yaml
from datetime import datetime

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lexicon_expansion.config.paths import (
    get_lexicon_path, get_expansion_root, get_output_dir,
    get_corpus_dir, get_config_path
)
from lexicon_expansion.scripts.extract_candidates import CandidateExtractor
from lexicon_expansion.scripts.category_manager import CategoryManager
from lexicon_expansion.scripts.merge_lexicons import LexiconMerger
from lexicon_expansion.scripts.validate_yaml import validate_candidate_file

def main():
    parser = argparse.ArgumentParser(
        description='JAIML辞書拡張パイプライン'
    )
    parser.add_argument(
        '--phase', 
        choices=['extract', 'validate', 'merge', 'split'],
        required=True,
        help='実行フェーズ'
    )
    parser.add_argument(
        '--config', 
        type=str,
        help='抽出ルール設定ファイル'
    )
    parser.add_argument(
        '--schema', 
        type=str,
        help='カテゴリスキーマファイル'
    )
    parser.add_argument(
        '--corpus', 
        type=str,
        help='入力コーパスファイル'
    )
    parser.add_argument(
        '--output', 
        type=str,
        help='出力ディレクトリ'
    )
    parser.add_argument(
        '--lexicon',
        type=str,
        help='辞書ファイルパス（split時のみ）'
    )
    parser.add_argument(
        '--categories',
        type=str,
        nargs='+',
        help='処理対象カテゴリ（extract時のみ）'
    )
    
    args = parser.parse_args()
    
    # デフォルトパスの設定
    config_path = args.config or str(get_config_path('extraction_rules.yaml'))
    schema_path = args.schema or str(get_config_path('category_schemas.yaml'))
    output_dir = Path(args.output) if args.output else get_output_dir()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if args.phase == 'extract':
        # コーパスパスの設定
        if args.corpus:
            corpus_path = Path(args.corpus)
            if not corpus_path.is_absolute():
                corpus_path = get_corpus_dir() / corpus_path
        else:
            # デフォルトコーパス
            corpus_path = get_corpus_dir() / 'SNOW_D18.txt'
            
        if not corpus_path.exists():
            print(f"エラー: コーパスファイルが見つかりません: {corpus_path}")
            sys.exit(1)
            
        # 候補抽出フェーズ
        extractor = CandidateExtractor(config_path)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f)
            
        # 処理対象カテゴリの決定
        target_categories = args.categories if args.categories else rules.keys()
        
        for category in target_categories:
            if category not in rules:
                print(f"警告: カテゴリ '{category}' は設定に存在しません")
                continue
                
            print(f"抽出中: {category}...")
            candidates = extractor.extract_category(str(corpus_path), category)
            
            # 出力ディレクトリの作成
            category_output_dir = output_dir / 'candidates' / category / 'raw'
            category_output_dir.mkdir(parents=True, exist_ok=True)
            
            output_data = {
                'metadata': {
                    'category': category,
                    'extracted_date': timestamp,
                    'corpus_file': corpus_path.name,
                    'total_candidates': len(candidates)
                },
                'candidates': [
                    {
                        'phrase': phrase,
                        'frequency': data.get('frequency', data) if isinstance(data, dict) else data,
                        'pos_patterns': data.get('pos_patterns', []) if isinstance(data, dict) else [],
                        'accept': None,
                        'note': None
                    }
                    for phrase, data in candidates.items()
                ]
            }
            
            output_path = category_output_dir / f'candidates_{timestamp}.yaml'
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(output_data, f, allow_unicode=True,
                        default_flow_style=False, sort_keys=False)
            print(f"  → 保存: {output_path}")
            print(f"  → 候補数: {len(candidates)}")
                        
    elif args.phase == 'validate':
        # 検証フェーズ
        reviewed_dir = output_dir / 'candidates'
        
        if not reviewed_dir.exists():
            print(f"エラー: 候補ディレクトリが存在しません: {reviewed_dir}")
            sys.exit(1)
            
        validation_results = []
        
        for category_dir in reviewed_dir.iterdir():
            if not category_dir.is_dir():
                continue
                
            reviewed_path = category_dir / 'reviewed'
            if reviewed_path.exists():
                for yaml_file in reviewed_path.glob('*.yaml'):
                    is_valid = validate_candidate_file(str(yaml_file))
                    status = "✓" if is_valid else "✗"
                    print(f"{status} {yaml_file.relative_to(output_dir)}")
                    validation_results.append({
                        'file': str(yaml_file),
                        'valid': is_valid
                    })
                        
        # 検証レポートの生成
        report_dir = output_dir / 'reports'
        report_dir.mkdir(exist_ok=True)
        report_path = report_dir / f'validation_report_{timestamp}.txt'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("辞書候補検証レポート\n")
            f.write(f"実行日時: {timestamp}\n")
            f.write("-" * 50 + "\n\n")
            
            valid_count = sum(1 for r in validation_results if r['valid'])
            f.write(f"検証ファイル数: {len(validation_results)}\n")
            f.write(f"有効: {valid_count}\n")
            f.write(f"無効: {len(validation_results) - valid_count}\n")
            
        print(f"\n検証レポート: {report_path}")
                        
    elif args.phase == 'merge':
        # 統合フェーズ
        lexicon_path = get_lexicon_path()
        merger = LexiconMerger(str(lexicon_path))
        
        reviewed_dir = output_dir / 'candidates'
        if not reviewed_dir.exists():
            print(f"エラー: レビュー済み候補が見つかりません: {reviewed_dir}")
            sys.exit(1)
            
        merged = merger.merge_reviewed_candidates(reviewed_dir)
        
        # 新バージョンの保存
        new_lexicon_path = lexicon_path.parent / f'jaiml_lexicons_{timestamp}.yaml'
        merger.save_merged_lexicon(str(new_lexicon_path), merged)
        
        print(f"統合完了: {new_lexicon_path}")
        
        # 差分レポートの生成
        from lexicon_expansion.version_control.version_manager import LexiconVersionManager
        version_manager = LexiconVersionManager(str(lexicon_path.parent))
        
        # 現在の辞書データを読み込み
        with open(new_lexicon_path, 'r', encoding='utf-8') as f:
            new_data = yaml.safe_load(f)
            
        version_file = version_manager.save_version(
            new_data,
            metadata={'action': 'merge', 'timestamp': timestamp}
        )
        print(f"バージョン保存: {version_file}")
        
    elif args.phase == 'split':
        # 分割フェーズ
        if args.lexicon:
            lexicon_path = Path(args.lexicon)
        else:
            lexicon_path = get_lexicon_path()
            
        if not lexicon_path.exists():
            print(f"エラー: 辞書ファイルが見つかりません: {lexicon_path}")
            sys.exit(1)
            
        categories_dir = lexicon_path.parent / 'categories'
        manager = CategoryManager(schema_path, str(categories_dir))
        manager.split_master_lexicon(str(lexicon_path))
        
        print(f"分割完了: {categories_dir}")
        
        # 分割結果の統計
        for category_type in ['pragmatic', 'lexical']:
            type_dir = categories_dir / category_type
            if type_dir.exists():
                files = list(type_dir.glob('*.yaml'))
                print(f"  {category_type}: {len(files)}カテゴリ")

if __name__ == '__main__':
    main()