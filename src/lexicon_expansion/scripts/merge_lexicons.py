import yaml
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime

class LexiconMerger:
    def __init__(self, base_lexicon_path: str):
        self.base_lexicon_path = Path(base_lexicon_path)
        if not self.base_lexicon_path.exists():
            raise FileNotFoundError(f"ベース辞書が見つかりません: {base_lexicon_path}")
            
        with open(self.base_lexicon_path, 'r', encoding='utf-8') as f:
            self.base_lexicon = yaml.safe_load(f) or {}
            
    def merge_reviewed_candidates(self, reviewed_dir: Path) -> Dict[str, List[str]]:
        """選別済み候補を統合"""
        if not reviewed_dir.exists():
            raise FileNotFoundError(f"レビューディレクトリが見つかりません: {reviewed_dir}")
            
        merged = {}
        merge_stats = {
            'total_added': 0,
            'total_skipped': 0,
            'categories_updated': 0
        }
        
        # ベース辞書をコピー
        for category, phrases in self.base_lexicon.items():
            if isinstance(phrases, list):
                merged[category] = list(phrases)
            else:
                # 辞書形式でない場合はスキップ
                print(f"警告: カテゴリ '{category}' は無効な形式です")
                
        for category_dir in reviewed_dir.iterdir():
            if not category_dir.is_dir():
                continue
                
            category = category_dir.name
            reviewed_path = category_dir / 'reviewed'
            
            if not reviewed_path.exists():
                continue
                
            # カテゴリが存在しない場合は新規作成
            if category not in merged:
                merged[category] = []
                
            category_added = 0
            category_skipped = 0
            
            # 各レビュー済みファイルを処理
            for yaml_file in sorted(reviewed_path.glob("*.yaml")):
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                        
                    if not data or 'candidates' not in data:
                        print(f"警告: 無効なファイル形式: {yaml_file}")
                        continue
                        
                    for candidate in data['candidates']:
                        if candidate.get('accept', False):
                            phrase = candidate['phrase']
                            if phrase not in merged[category]:
                                merged[category].append(phrase)
                                category_added += 1
                            else:
                                category_skipped += 1
                                
                except Exception as e:
                    print(f"エラー: {yaml_file} の処理中: {e}")
                    
            if category_added > 0:
                merge_stats['categories_updated'] += 1
                print(f"  {category}: +{category_added}件 追加 ({category_skipped}件 重複)")
                
            merge_stats['total_added'] += category_added
            merge_stats['total_skipped'] += category_skipped
        
        # 統計の表示
        print(f"\n統合統計:")
        print(f"  更新カテゴリ数: {merge_stats['categories_updated']}")
        print(f"  追加総数: {merge_stats['total_added']}")
        print(f"  重複スキップ数: {merge_stats['total_skipped']}")
        
        return merged
    
    def save_merged_lexicon(self, output_path: str, merged_data: Dict):
        """統合辞書を保存"""
        output_path = Path(output_path)
        
        # 出力ディレクトリの作成
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # バックアップの作成
        if output_path.exists():
            backup_path = output_path.with_suffix(
                f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.yaml'
            )
            output_path.rename(backup_path)
            print(f"既存ファイルをバックアップ: {backup_path}")
        
        # データの整形とソート
        sorted_data = {}
        for category in sorted(merged_data.keys()):
            if isinstance(merged_data[category], list):
                # 重複除去とソート
                unique_phrases = sorted(list(set(merged_data[category])))
                sorted_data[category] = unique_phrases
            else:
                sorted_data[category] = merged_data[category]
                
        # 保存
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(sorted_data, f, allow_unicode=True, 
                     default_flow_style=False, sort_keys=True)
                     
        # 統計情報の出力
        total_phrases = sum(
            len(phrases) for phrases in sorted_data.values() 
            if isinstance(phrases, list)
        )
        print(f"\n保存完了: {output_path}")
        print(f"  カテゴリ数: {len(sorted_data)}")
        print(f"  総語彙数: {total_phrases}")
        
    def generate_merge_report(self, merged_data: Dict) -> str:
        """統合レポートの生成"""
        report = []
        report.append("# 辞書統合レポート")
        report.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 既存辞書との比較
        report.append("## カテゴリ別統計")
        report.append("")
        report.append("| カテゴリ | 既存 | 統合後 | 増減 |")
        report.append("|----------|------|--------|------|")
        
        total_before = 0
        total_after = 0
        
        all_categories = set(list(self.base_lexicon.keys()) + list(merged_data.keys()))
        
        for category in sorted(all_categories):
            before = len(self.base_lexicon.get(category, []))
            after = len(merged_data.get(category, []))
            diff = after - before
            
            total_before += before
            total_after += after
            
            diff_str = f"+{diff}" if diff > 0 else str(diff)
            report.append(f"| {category} | {before} | {after} | {diff_str} |")
            
        # 合計行
        total_diff = total_after - total_before
        diff_str = f"+{total_diff}" if total_diff > 0 else str(total_diff)
        report.append(f"| **合計** | **{total_before}** | **{total_after}** | **{diff_str}** |")
        
        return "\n".join(report)