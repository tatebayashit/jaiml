import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class LexiconVersionManager:
    def __init__(self, lexicon_dir: str = "lexicons"):
        self.lexicon_dir = Path(lexicon_dir)
        self.version_dir = self.lexicon_dir / "versions"
        self.version_dir.mkdir(parents=True, exist_ok=True)
        self.changelog_path = self.version_dir / "changelog.json"
        
    def save_version(self, lexicon_data: Dict, metadata: Optional[Dict] = None) -> str:
        """新バージョンの保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_file = self.version_dir / f"jaiml_lexicons_{timestamp}.yaml"
        
        # 辞書データ保存
        with open(version_file, 'w', encoding='utf-8') as f:
            yaml.dump(lexicon_data, f, allow_unicode=True, 
                     default_flow_style=False, sort_keys=True)
        
        # 変更ログ更新
        self._update_changelog(timestamp, lexicon_data, metadata)
        
        return str(version_file)
    
    def _load_changelog(self) -> Dict:
        """変更ログの読み込み"""
        if self.changelog_path.exists():
            with open(self.changelog_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"versions": []}
    
    def _update_changelog(self, timestamp: str, lexicon_data: Dict, metadata: Optional[Dict]):
        """変更ログの更新"""
        changelog = self._load_changelog()
        
        # 前バージョンとの差分計算
        prev_version = self._get_latest_version()
        if prev_version:
            diff_stats = self._calculate_diff(prev_version, lexicon_data)
        else:
            diff_stats = self._calculate_initial_stats(lexicon_data)
        
        entry = {
            "timestamp": timestamp,
            "metadata": metadata or {},
            "statistics": diff_stats,
            "coverage_metrics": self._calculate_coverage(lexicon_data)
        }
        
        changelog["versions"].append(entry)
        
        with open(self.changelog_path, 'w', encoding='utf-8') as f:
            json.dump(changelog, f, ensure_ascii=False, indent=2)
    
    def _get_latest_version(self) -> Optional[Dict]:
        """最新バージョンの取得"""
        version_files = sorted(self.version_dir.glob("jaiml_lexicons_*.yaml"))
        if not version_files:
            return None
            
        # 最新ファイルを読み込み
        with open(version_files[-1], 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _calculate_initial_stats(self, lexicon_data: Dict) -> Dict:
        """初期統計の計算"""
        stats = {}
        for category, phrases in lexicon_data.items():
            if isinstance(phrases, list):
                stats[category] = {
                    "added": phrases,
                    "removed": [],
                    "total_before": 0,
                    "total_after": len(phrases),
                    "change_rate": 1.0
                }
        return stats
    
    def _calculate_diff(self, prev_data: Dict, curr_data: Dict) -> Dict:
        """バージョン間差分の計算"""
        diff_stats = {}
        
        all_categories = set(list(prev_data.keys()) + list(curr_data.keys()))
        
        for category in all_categories:
            prev_items = set(prev_data.get(category, []))
            curr_items = set(curr_data.get(category, []))
            
            added = list(curr_items - prev_items)
            removed = list(prev_items - curr_items)
            
            diff_stats[category] = {
                "added": sorted(added),
                "removed": sorted(removed),
                "total_before": len(prev_items),
                "total_after": len(curr_items),
                "change_rate": (len(curr_items) - len(prev_items)) / max(len(prev_items), 1)
            }
            
        return diff_stats
    
    def _calculate_coverage(self, lexicon_data: Dict) -> Dict:
        """カバレッジ指標の計算"""
        all_phrases = []
        for phrases in lexicon_data.values():
            if isinstance(phrases, list):
                all_phrases.extend(phrases)
                
        if not all_phrases:
            return {
                "total_phrases": 0,
                "category_distribution": {},
                "avg_phrase_length": 0,
                "unique_characters": 0
            }
            
        coverage = {
            "total_phrases": len(all_phrases),
            "category_distribution": {
                cat: len(phrases) for cat, phrases in lexicon_data.items()
                if isinstance(phrases, list)
            },
            "avg_phrase_length": sum(len(p) for p in all_phrases) / len(all_phrases),
            "unique_characters": len(set(''.join(all_phrases)))
        }
        return coverage
    
    def _calculate_avg_length(self, lexicon_data: Dict) -> float:
        """平均フレーズ長の計算"""
        all_lengths = []
        for phrases in lexicon_data.values():
            if isinstance(phrases, list):
                all_lengths.extend(len(p) for p in phrases)
        
        if not all_lengths:
            return 0.0
            
        return sum(all_lengths) / len(all_lengths)
    
    def _load_version(self, version_name: str) -> Dict:
        """特定バージョンの読み込み"""
        version_path = self.version_dir / f"{version_name}.yaml"
        if not version_path.exists():
            version_path = self.version_dir / version_name
            
        if not version_path.exists():
            raise FileNotFoundError(f"バージョンファイルが見つかりません: {version_name}")
            
        with open(version_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def generate_diff_report(self, version1: str, version2: str) -> str:
        """バージョン間の詳細差分レポート生成"""
        v1_data = self._load_version(version1)
        v2_data = self._load_version(version2)
        
        report = f"# 辞書差分レポート\n\n"
        report += f"比較: {version1} → {version2}\n\n"
        
        # 統計サマリー
        diff_stats = self._calculate_diff(v1_data, v2_data)
        total_added = sum(len(s['added']) for s in diff_stats.values())
        total_removed = sum(len(s['removed']) for s in diff_stats.values())
        
        report += f"## 全体統計\n\n"
        report += f"- 追加総数: {total_added}件\n"
        report += f"- 削除総数: {total_removed}件\n"
        report += f"- 変更カテゴリ数: {sum(1 for s in diff_stats.values() if s['added'] or s['removed'])}件\n\n"
        
        # カテゴリ別詳細
        for category in sorted(diff_stats.keys()):
            stats = diff_stats[category]
            
            if stats['added'] or stats['removed']:
                report += f"## {category}\n\n"
                report += f"- 変更前: {stats['total_before']}件\n"
                report += f"- 変更後: {stats['total_after']}件\n"
                report += f"- 変化率: {stats['change_rate']:+.1%}\n\n"
                
                if stats['added']:
                    report += f"### 追加 ({len(stats['added'])}件)\n"
                    for item in stats['added'][:10]:  # 最初の10件のみ表示
                        report += f"+ {item}\n"
                    if len(stats['added']) > 10:
                        report += f"... 他 {len(stats['added']) - 10}件\n"
                    report += "\n"
                    
                if stats['removed']:
                    report += f"### 削除 ({len(stats['removed'])}件)\n"
                    for item in stats['removed'][:10]:  # 最初の10件のみ表示
                        report += f"- {item}\n"
                    if len(stats['removed']) > 10:
                        report += f"... 他 {len(stats['removed']) - 10}件\n"
                    report += "\n"
                    
        return report