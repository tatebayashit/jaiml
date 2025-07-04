import argparse
from pathlib import Path
import yaml
from datetime import datetime

from extract_candidates import CandidateExtractor
from category_manager import CategoryManager
from merge_lexicons import LexiconMerger
from validate_yaml import validate_candidate_file

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['extract', 'validate', 'merge', 'split'])
    parser.add_argument('--config', default='config/extraction_rules.yaml')
    parser.add_argument('--schema', default='config/category_schemas.yaml')
    parser.add_argument('--corpus', default='corpus/SNOW_D18.txt')
    parser.add_argument('--output', default='outputs/')
    args = parser.parse_args()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if args.phase == 'extract':
        # 候補抽出フェーズ
        extractor = CandidateExtractor(args.config)
        with open(args.config, 'r') as f:
            rules = yaml.safe_load(f)
            
        for category in rules.keys():
            print(f"Extracting {category}...")
            candidates = extractor.extract_category(args.corpus, category)
            
            output_dir = Path(args.output) / 'candidates' / category / 'raw'
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_data = {
                'metadata': {
                    'category': category,
                    'extracted_date': timestamp,
                    'total_candidates': len(candidates)
                },
                'candidates': [
                    {
                        'phrase': phrase,
                        'frequency': data.get('frequency', data),
                        'pos_patterns': data.get('pos_patterns', []),
                        'accept': None
                    }
                    for phrase, data in candidates.items()
                ]
            }
            
            output_path = output_dir / f'candidates_{timestamp}.yaml'
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(output_data, f, allow_unicode=True,
                        default_flow_style=False)
                        
    elif args.phase == 'validate':
        # 検証フェーズ
        manager = CategoryManager(args.schema, args.output)
        reviewed_dir = Path(args.output) / 'candidates'
        
        for category_dir in reviewed_dir.iterdir():
            if not category_dir.is_dir():
                continue
                
            reviewed_path = category_dir / 'reviewed'
            if reviewed_path.exists():
                for yaml_file in reviewed_path.glob('*.yaml'):
                    if validate_candidate_file(str(yaml_file)):
                        print(f"✓ {yaml_file}")
                    else:
                        print(f"✗ {yaml_file}")
                        
    elif args.phase == 'merge':
        # 統合フェーズ
        merger = LexiconMerger('lexicons/jaiml_lexicons.yaml')
        reviewed_dir = Path(args.output) / 'candidates'
        merged = merger.merge_reviewed_candidates(reviewed_dir)
        
        output_path = f'lexicons/jaiml_lexicons_{timestamp}.yaml'
        merger.save_merged_lexicon(output_path, merged)
        
    elif args.phase == 'split':
        # 分割フェーズ
        manager = CategoryManager(args.schema, 'lexicons/categories')
        manager.split_master_lexicon('lexicons/jaiml_lexicons.yaml')

if __name__ == '__main__':
    main()