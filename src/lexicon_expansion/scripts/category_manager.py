from pathlib import Path
import yaml
from typing import Dict, List, Optional

class CategoryManager:
    """カテゴリ別辞書の管理"""
    
    def __init__(self, schema_path: str, lexicon_dir: str):
        with open(schema_path, 'r', encoding='utf-8') as f:
            self.schema = yaml.safe_load(f)
        self.lexicon_dir = Path(lexicon_dir)
        self.lexicon_dir.mkdir(exist_ok=True)
        
    def split_master_lexicon(self, master_path: str):
        """マスター辞書をカテゴリ別に分割"""
        with open(master_path, 'r', encoding='utf-8') as f:
            master_data = yaml.safe_load(f)
            
        for category_type in ['pragmatic', 'lexical']:
            type_dir = self.lexicon_dir / category_type
            type_dir.mkdir(exist_ok=True)
            
            for category in self.schema['categories'][category_type]:
                if category in master_data:
                    category_data = {
                        'metadata': {
                            'category': category,
                            'type': category_type,
                            'schema': self.schema['categories'][category_type][category]
                        },
                        'phrases': master_data[category]
                    }
                    
                    output_path = type_dir / f"{category}.yaml"
                    with open(output_path, 'w', encoding='utf-8') as f:
                        yaml.dump(category_data, f, allow_unicode=True,
                                default_flow_style=False)
    
    def merge_category_lexicons(self, output_path: str):
        """カテゴリ別辞書を統合"""
        merged_data = {}
        
        for category_type in ['pragmatic', 'lexical']:
            type_dir = self.lexicon_dir / category_type
            if not type_dir.exists():
                continue
                
            for yaml_file in type_dir.glob("*.yaml"):
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    
                category = data['metadata']['category']
                merged_data[category] = data['phrases']
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(merged_data, f, allow_unicode=True,
                    default_flow_style=False, sort_keys=True)
    
    def validate_category(self, category: str, phrases: List[str]) -> Dict[str, List[str]]:
        """カテゴリ別検証"""
        # カテゴリタイプの特定
        category_type = None
        for c_type in ['pragmatic', 'lexical']:
            if category in self.schema['categories'][c_type]:
                category_type = c_type
                break
                
        if not category_type:
            return {'error': [f'Unknown category: {category}']}
            
        category_schema = self.schema['categories'][category_type][category]
        validation_errors = []
        
        # 長さ制限チェック
        max_length = category_schema.get('max_length', 50)
        for phrase in phrases:
            if len(phrase) > max_length:
                validation_errors.append(
                    f'Phrase too long ({len(phrase)} > {max_length}): {phrase}'
                )
        
        # カスタム検証ルール適用
        if 'validation' in category_schema:
            for rule_name in category_schema['validation']:
                errors = self._apply_validation_rule(rule_name, phrases)
                validation_errors.extend(errors)
                
        return {'errors': validation_errors}