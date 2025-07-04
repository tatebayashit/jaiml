import numpy as np
import fasttext
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
import umap

class SemanticClusterer:
    def __init__(self, model_path: str = None):
        # 事前学習済み日本語fastTextモデル使用
        if model_path:
            self.model = fasttext.load_model(model_path)
        else:
            # 日本語Wikipediaで学習済みモデルをダウンロード
            self._download_pretrained_model()
            
    def _download_pretrained_model(self):
        """事前学習済みモデルのダウンロード"""
        import urllib.request
        import zipfile
        
        url = "https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.ja.300.bin.gz"
        # 実装省略: ダウンロードと解凍処理
        
    def vectorize_phrases(self, phrases: List[str]) -> np.ndarray:
        """フレーズのベクトル化"""
        vectors = []
        for phrase in phrases:
            # 文全体のベクトルを取得
            vec = self.model.get_sentence_vector(phrase)
            vectors.append(vec)
        return np.array(vectors)
    
    def cluster_by_similarity(self, category: str, phrases: List[str], 
                            method: str = 'hierarchical') -> Dict:
        """意味的類似性に基づくクラスタリング"""
        vectors = self.vectorize_phrases(phrases)
        
        if method == 'hierarchical':
            # 階層的クラスタリング
            clustering = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=0.5,
                metric='cosine',
                linkage='average'
            )
        else:
            # DBSCAN
            clustering = DBSCAN(
                eps=0.3,
                min_samples=2,
                metric='cosine'
            )
            
        labels = clustering.fit_predict(vectors)
        
        # クラスタごとにグループ化
        clusters = {}
        for idx, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(phrases[idx])
            
        # クラスタ統計
        cluster_stats = self._analyze_clusters(clusters, vectors, labels)
        
        return {
            "clusters": clusters,
            "statistics": cluster_stats,
            "vectors": vectors,
            "labels": labels
        }
    
    def _analyze_clusters(self, clusters: Dict, vectors: np.ndarray, 
                         labels: np.ndarray) -> Dict:
        """クラスタ統計分析"""
        stats = {}
        
        for label, members in clusters.items():
            if label == -1:  # ノイズ点
                continue
                
            cluster_indices = np.where(labels == label)[0]
            cluster_vectors = vectors[cluster_indices]
            
            # クラスタ内類似度
            if len(cluster_vectors) > 1:
                similarity_matrix = cosine_similarity(cluster_vectors)
                avg_similarity = np.mean(similarity_matrix[np.triu_indices_from(
                    similarity_matrix, k=1
                )])
            else:
                avg_similarity = 1.0
                
            # 中心性の高いフレーズ（代表語）
            if len(cluster_vectors) > 1:
                centroid = np.mean(cluster_vectors, axis=0)
                distances = [cosine_similarity([vec], [centroid])[0][0] 
                           for vec in cluster_vectors]
                representative_idx = np.argmax(distances)
                representative = members[representative_idx]
            else:
                representative = members[0]
                
            stats[label] = {
                "size": len(members),
                "avg_similarity": float(avg_similarity),
                "representative": representative,
                "cohesion": float(np.std(cluster_vectors))  # 凝集度
            }
            
        return stats
    
    def visualize_clusters(self, result: Dict, output_path: str):
        """クラスタの可視化"""
        vectors = result["vectors"]
        labels = result["labels"]
        
        # UMAP次元削減
        reducer = umap.UMAP(n_components=2, random_state=42)
        embedding = reducer.fit_transform(vectors)
        
        # プロット
        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(
            embedding[:, 0], 
            embedding[:, 1], 
            c=labels, 
            cmap='tab20',
            alpha=0.6
        )
        
        # クラスタ代表語をラベル表示
        for label, stats in result["statistics"].items():
            if label == -1:
                continue
            cluster_points = embedding[labels == label]
            center = cluster_points.mean(axis=0)
            plt.annotate(
                stats["representative"],
                xy=center,
                fontsize=9,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.5)
            )
            
        plt.colorbar(scatter)
        plt.title('語彙クラスタの意味空間分布')
        plt.savefig(output_path)