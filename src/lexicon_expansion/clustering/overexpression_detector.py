# overexpression_detector.py
from collections import Counter
import numpy as np
from typing import Dict, List, Set

class OverexpressionDetector:
    def __init__(self, clusterer: SemanticClusterer):
        self.clusterer = clusterer
        
    def detect_redundant_patterns(self, lexicon_data: Dict, 
                                corpus_stats: Dict) -> Dict:
        """過剰表現パターンの検出"""
        results = {}
        
        for category, phrases in lexicon_data.items():
            # クラスタリング実行
            cluster_result = self.clusterer.cluster_by_similarity(
                category, phrases
            )
            
            # 各クラスタのTF-IDF分析
            redundancies = []
            
            for label, cluster_phrases in cluster_result["clusters"].items():
                if label == -1 or len(cluster_phrases) < 3:
                    continue
                    
                # クラスタ内のTF-IDF分散を計算
                tfidf_variance = self._calculate_tfidf_variance(
                    cluster_phrases, corpus_stats
                )
                
                # 低分散 = 過剰な類似表現
                if tfidf_variance < 0.1:
                    redundancies.append({
                        "cluster_id": label,
                        "phrases": cluster_phrases,
                        "variance": tfidf_variance,
                        "representative": cluster_result["statistics"][label]["representative"],
                        "severity": "high" if tfidf_variance < 0.05 else "medium"
                    })
                    
            results[category] = {
                "redundant_clusters": redundancies,
                "total_clusters": len(cluster_result["clusters"]),
                "redundancy_rate": len(redundancies) / max(len(cluster_result["clusters"]), 1)
            }
            
        return results
    
    def _calculate_tfidf_variance(self, phrases: List[str], 
                                 corpus_stats: Dict) -> float:
        """クラスタ内TF-IDF分散の計算"""
        # 簡易実装: 実際はコーパス統計が必要
        phrase_lengths = [len(p) for p in phrases]
        char_overlap = len(set(''.join(phrases))) / sum(phrase_lengths)
        
        # 文字重複率が高いほど分散は低い
        return char_overlap