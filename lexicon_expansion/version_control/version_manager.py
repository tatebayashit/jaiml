# version_manager.py
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import difflib

class LexiconVersionManager:
    def __init__(self, lexicon_dir: str = "lexicons"):
        self.lexicon_dir = Path(lexicon_dir)
        self.version_dir = self.lexicon_dir / "versions"
        self.version_dir.mkdir(exist_ok=True)
        self.changelog_path = self.version_dir / "changelog.json"
        
    def save_version(self, lexicon_data: Dict, metadata: Dict = None) -> str:
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
    
    def _update_changelog(self, timestamp: str, lexicon_data: Dict, metadata: Dict):
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
    
    def _calculate_diff(self, prev_data: Dict, curr_data: Dict) -> Dict:
        """バージョン間差分の計算"""
        diff_stats = {}
        
        for category in set(list(prev_data.keys()) + list(curr_data.keys())):
            prev_items = set(prev_data.get(category, []))
            curr_items = set(curr_data.get(category, []))
            
            diff_stats[category] = {
                "added": list(curr_items - prev_items),
                "removed": list(prev_items - curr_items),
                "total_before": len(prev_items),
                "total_after": len(curr_items),
                "change_rate": (len(curr_items) - len(prev_items)) / max(len(prev_items), 1)
            }
            
        return diff_stats
    
    def _calculate_coverage(self, lexicon_data: Dict) -> Dict:
        """カバレッジ指標の計算"""
        coverage = {
            "total_phrases": sum(len(phrases) for phrases in lexicon_data.values()),
            "category_distribution": {
                cat: len(phrases) for cat, phrases in lexicon_data.items()
            },
            "avg_phrase_length": self._calculate_avg_length(lexicon_data),
            "unique_characters": len(set(''.join(
                phrase for phrases in lexicon_data.values() for phrase in phrases
            )))
        }
        return coverage
    
    def generate_diff_report(self, version1: str, version2: str) -> str:
        """バージョン間の詳細差分レポート生成"""
        v1_data = self._load_version(version1)
        v2_data = self._load_version(version2)
        
        report = f"# 辞書差分レポート\n\n"
        report += f"比較: {version1} → {version2}\n\n"
        
        for category in sorted(set(list(v1_data.keys()) + list(v2_data.keys()))):
            v1_items = set(v1_data.get(category, []))
            v2_items = set(v2_data.get(category, []))
            
            added = v2_items - v1_items
            removed = v1_items - v2_items
            
            if added or removed:
                report += f"## {category}\n\n"
                
                if added:
                    report += f"### 追加 ({len(added)}件)\n"
                    for item in sorted(added):
                        report += f"+ {item}\n"
                    report += "\n"
                    
                if removed:
                    report += f"### 削除 ({len(removed)}件)\n"
                    for item in sorted(removed):
                        report += f"- {item}\n"
                    report += "\n"
                    
        return report