import json
from pathlib import Path
from typing import Dict, List, Optional

from .auto_annotator import AutoAnnotator, AnnotationCandidate

class SnippetGenerator:
    def __init__(self, annotator: AutoAnnotator):
        self.annotator = annotator
        
    def extract_snippets(self, corpus_path: str, 
                        output_dir: str,
                        snippet_length: int = 200):
        """アノテーション候補周辺のスニペット抽出"""
        corpus_path = Path(corpus_path)
        output_dir = Path(output_dir)
        
        if not corpus_path.exists():
            raise FileNotFoundError(f"コーパスファイルが見つかりません: {corpus_path}")
            
        output_dir.mkdir(parents=True, exist_ok=True)
        
        snippets_by_category = {}
        
        with open(corpus_path, 'r', encoding='utf-8') as f:
            for line_no, line in enumerate(f):
                if not line.strip():
                    continue
                    
                try:
                    data = json.loads(line)
                    user_text = data.get('user', '')
                    response_text = data.get('response', '')
                except json.JSONDecodeError:
                    # JSON形式でない場合はスキップ
                    continue
                except Exception as e:
                    print(f"警告: 行 {line_no + 1} の処理中にエラー: {e}")
                    continue
                    
                if not response_text:
                    continue
                
                candidates = self.annotator.annotate_text(response_text)
                
                for candidate in candidates:
                    category = candidate.category
                    if category not in snippets_by_category:
                        snippets_by_category[category] = []
                        
                    # スニペット範囲の計算
                    snippet_start = max(0, candidate.start - snippet_length // 2)
                    snippet_end = min(len(response_text), 
                                    candidate.end + snippet_length // 2)
                    
                    # スニペットデータの構築
                    snippet = {
                        "snippet_id": f"snippet_{line_no}_{candidate.start}",
                        "text": response_text[snippet_start:snippet_end],
                        "phrase": candidate.phrase,
                        "phrase_start": candidate.start - snippet_start,
                        "phrase_end": candidate.end - snippet_start,
                        "context": {
                            "user": user_text,
                            "full_response": response_text,
                            "dialogue_id": line_no
                        },
                        "metadata": {
                            "confidence": candidate.confidence,
                            "category": category,
                            "original_start": candidate.start,
                            "original_end": candidate.end
                        }
                    }
                    
                    # 前後の文脈も含める（オプション）
                    if snippet_start > 0:
                        snippet["prefix_ellipsis"] = True
                    if snippet_end < len(response_text):
                        snippet["suffix_ellipsis"] = True
                    
                    snippets_by_category[category].append(snippet)
        
        # カテゴリ別に保存
        saved_files = []
        for category, snippets in snippets_by_category.items():
            output_path = output_dir / f"{category}_snippets.jsonl"
            
            # 重複除去（同一フレーズ・同一文脈の場合）
            unique_snippets = self._remove_duplicate_snippets(snippets)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for snippet in unique_snippets:
                    f.write(json.dumps(snippet, ensure_ascii=False) + '\n')
                    
            saved_files.append({
                'path': output_path,
                'category': category,
                'count': len(unique_snippets)
            })
            
        # サマリーファイルの生成
        summary_path = output_dir / 'snippets_summary.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            summary = {
                'corpus': corpus_path.name,
                'total_categories': len(snippets_by_category),
                'total_snippets': sum(s['count'] for s in saved_files),
                'categories': {
                    s['category']: {
                        'file': s['path'].name,
                        'count': s['count']
                    } for s in saved_files
                }
            }
            json.dump(summary, f, ensure_ascii=False, indent=2)
            
        print(f"スニペット抽出完了: {len(saved_files)}カテゴリ")
        for file_info in saved_files:
            print(f"  - {file_info['category']}: {file_info['count']}件")
            
    def _remove_duplicate_snippets(self, snippets: List[Dict]) -> List[Dict]:
        """重複スニペットの除去"""
        seen = set()
        unique_snippets = []
        
        for snippet in snippets:
            # 重複判定用のキー（フレーズと周辺テキストのハッシュ）
            key = (
                snippet['phrase'],
                snippet['text'][max(0, snippet['phrase_start']-20):
                              min(len(snippet['text']), snippet['phrase_end']+20)]
            )
            
            if key not in seen:
                seen.add(key)
                unique_snippets.append(snippet)
                
        return unique_snippets