from pathlib import Path
import yaml
from typing import Dict, List, Optional
import re

class CategoryManager:
    """カテゴリ別辞書の管理"""
    
    def __init__(self, schema_path: str, lexicon_dir: str):
        schema_path = Path(schema_path)
        if not schema_path.exists():
            raise FileNotFoundError(f"スキーマファイルが見つかりません: {schema_path}")
            
        with open(schema_path, 'r', encoding='utf-8') as f:
            self.schema = yaml.safe_load(f)
            
        self.lexicon_dir = Path(lexicon_dir)
        self.lexicon_dir.mkdir(parents=True, exist_ok=True)
        
    def split_master_lexicon(self, master_path: str):
        """マスター辞書をカテゴリ別に分割"""
        master_path = Path(master_path)
        if not master_path.exists():
            raise FileNotFoundError(f"マスター辞書が見つかりません: {master_path}")
            
        with open(master_path, 'r', encoding='utf-8') as f:
            master_data = yaml.safe_load(f)
            
        # カテゴリタイプ別に分割
        for category_type in ['pragmatic', 'lexical']:
            type_dir = self.lexicon_dir / category_type
            type_dir.mkdir(exist_ok=True)
            
            if category_type not in self.schema.get('categories', {}):
                print(f"警告: カテゴリタイプ '{category_type}' がスキーマに存在しません")
                continue
                
            for category in self.schema['categories'][category_type]:
                if category in master_data:
                    category_data = {
                        'metadata': {
                            'category': category,
                            'type': category_type,
                            'schema': self.schema['categories'][category_type][category],
                            'phrase_count': len(master_data[category])
                        },
                        'phrases': sorted(master_data[category])  # ソートして保存
                    }
                    
                    output_path = type_dir / f"{category}.yaml"
                    with open(output_path, 'w', encoding='utf-8') as f:
                        yaml.dump(category_data, f, allow_unicode=True,
                                default_flow_style=False, sort_keys=False)
                    print(f"  分割: {output_path.relative_to(self.lexicon_dir)} ({len(master_data[category])}語)")
    
    def merge_category_lexicons(self, output_path: str):
        """カテゴリ別辞書を統合"""
        output_path = Path(output_path)
        merged_data = {}
        
        for category_type in ['pragmatic', 'lexical']:
            type_dir = self.lexicon_dir / category_type
            if not type_dir.exists():
                continue
                
            for yaml_file in type_dir.glob("*.yaml"):
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    
                if 'metadata' in data and 'phrases' in data:
                    category = data['metadata']['category']
                    merged_data[category] = data['phrases']
                else:
                    # 後方互換性のための処理
                    category = yaml_file.stem
                    merged_data[category] = data
        
        # アルファベット順にソート
        sorted_data = {k: sorted(v) if isinstance(v, list) else v 
                      for k, v in sorted(merged_data.items())}
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(sorted_data, f, allow_unicode=True,
                    default_flow_style=False, sort_keys=True)
                    
        print(f"統合完了: {output_path}")
        print(f"  カテゴリ数: {len(sorted_data)}")
        print(f"  総語彙数: {sum(len(v) for v in sorted_data.values() if isinstance(v, list))}")
    
    def validate_category(self, category: str, phrases: List[str]) -> Dict[str, List[str]]:
        """カテゴリ別検証"""
        # カテゴリタイプの特定
        category_type = None
        for c_type in ['pragmatic', 'lexical']:
            if (c_type in self.schema.get('categories', {}) and 
                category in self.schema['categories'][c_type]):
                category_type = c_type
                break
                
        if not category_type:
            return {'errors': [f'未知のカテゴリ: {category}']}
            
        category_schema = self.schema['categories'][category_type][category]
        validation_errors = []
        
        # 長さ制限チェック
        max_length = category_schema.get('max_length', 50)
        for phrase in phrases:
            if len(phrase) > max_length:
                validation_errors.append(
                    f'フレーズが長すぎます ({len(phrase)} > {max_length}): {phrase}'
                )
        
        # カスタム検証ルール適用
        if 'validation' in category_schema:
            for rule_name in category_schema['validation']:
                errors = self._apply_validation_rule(rule_name, phrases)
                validation_errors.extend(errors)
                
        return {'errors': validation_errors}
        
    def _apply_validation_rule(self, rule_name: str, phrases: List[str]) -> List[str]:
        """検証ルールの適用"""
        errors = []
        
        if 'validation_rules' not in self.schema:
            return errors
            
        if rule_name not in self.schema['validation_rules']:
            errors.append(f"未定義の検証ルール: {rule_name}")
            return errors
            
        rule = self.schema['validation_rules'][rule_name]
        
        # パターンチェック
        if 'patterns' in rule:
            for phrase in phrases:
                has_pattern = any(pattern in phrase for pattern in rule['patterns'])
                if not has_pattern:
                    errors.append(
                        f"必須パターンが見つかりません ({rule_name}): {phrase}"
                    )
                    
        # キーワードチェック
        if 'keywords' in rule:
            for phrase in phrases:
                has_keyword = any(keyword in phrase for keyword in rule['keywords'])
                if rule_name == 'semantic_negativity_check' and not has_keyword:
                    errors.append(
                        f"否定的意味要素が見つかりません: {phrase}"
                    )
                    
        return errors