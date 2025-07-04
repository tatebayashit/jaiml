# snippet_generator.py
class SnippetGenerator:
    def __init__(self, annotator: AutoAnnotator):
        self.annotator = annotator
        
    def extract_snippets(self, corpus_path: str, 
                        output_dir: str,
                        snippet_length: int = 200):
        """アノテーション候補周辺のスニペット抽出"""
        snippets_by_category = {}
        
        with open(corpus_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                response = data.get('response', '')
                
                candidates = self.annotator.annotate_text(response)
                
                for candidate in candidates:
                    category = candidate.category
                    if category not in snippets_by_category:
                        snippets_by_category[category] = []
                        
                    # スニペット抽出
                    snippet_start = max(0, candidate.start - snippet_length // 2)
                    snippet_end = min(len(response), 
                                    candidate.end + snippet_length // 2)
                    
                    snippet = {
                        "text": response[snippet_start:snippet_end],
                        "phrase": candidate.phrase,
                        "phrase_start": candidate.start - snippet_start,
                        "phrase_end": candidate.end - snippet_start,
                        "context": {
                            "user": data.get('user', ''),
                            "full_response": response
                        },
                        "metadata": {
                            "confidence": candidate.confidence,
                            "category": category
                        }
                    }
                    
                    snippets_by_category[category].append(snippet)
        
        # カテゴリ別に保存
        for category, snippets in snippets_by_category.items():
            output_path = Path(output_dir) / f"{category}_snippets.jsonl"
            with open(output_path, 'w', encoding='utf-8') as f:
                for snippet in snippets:
                    f.write(json.dumps(snippet, ensure_ascii=False) + '\n')