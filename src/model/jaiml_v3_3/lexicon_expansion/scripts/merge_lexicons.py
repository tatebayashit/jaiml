import yaml
from pathlib import Path
from typing import Dict, List

class LexiconMerger:
    def __init__(self, base_lexicon_path: str):
        with open(base_lexicon_path, 'r', encoding='utf-8') as f:
            self.base_lexicon = yaml.safe_load(f)
            
    def merge_reviewed_candidates(self, reviewed_dir: Path) -> Dict[str, List[str]]:
        """選別済み候補を統合"""
        merged = {}
        
        for category_dir in reviewed_dir.iterdir():
            if not category_dir.is_dir():
                continue
                
            category = category_dir.name
            merged[category] = list(self.base_lexicon.get(category, []))
            
            # 各レビュー済みファイルを処理
            for yaml_file in category_dir.glob("*.yaml"):
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    
                for candidate in data['candidates']:
                    if candidate.get('accept', False):
                        phrase = candidate['phrase']
                        if phrase not in merged[category]:
                            merged[category].append(phrase)
        
        return merged
    
    def save_merged_lexicon(self, output_path: str, merged_data: Dict):
        """統合辞書を保存"""
        # 既存辞書に統合
        for category, phrases in merged_data.items():
            self.base_lexicon[category] = sorted(list(set(phrases)))
            
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.base_lexicon, f, allow_unicode=True, 
                     default_flow_style=False, sort_keys=True)