# trend_analyzer.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict

class LexiconTrendAnalyzer:
    def __init__(self, version_manager: LexiconVersionManager):
        self.version_manager = version_manager
        
    def analyze_growth_trend(self) -> pd.DataFrame:
        """語彙成長トレンドの分析"""
        changelog = self.version_manager._load_changelog()
        
        trends = []
        for version in changelog["versions"]:
            timestamp = pd.to_datetime(version["timestamp"], format="%Y%m%d_%H%M%S")
            
            for category, stats in version["statistics"].items():
                trends.append({
                    "timestamp": timestamp,
                    "category": category,
                    "total": stats.get("total_after", 0),
                    "change_rate": stats.get("change_rate", 0)
                })
                
        return pd.DataFrame(trends)
    
    def plot_coverage_evolution(self, output_path: str):
        """カバレッジ推移の可視化"""
        df = self.analyze_growth_trend()
        
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        
        # 総語彙数の推移
        pivot_total = df.pivot(index='timestamp', columns='category', values='total')
        pivot_total.plot(ax=axes[0], marker='o')
        axes[0].set_title('カテゴリ別語彙数推移')
        axes[0].set_ylabel('語彙数')
        
        # 変化率の推移
        pivot_rate = df.pivot(index='timestamp', columns='category', values='change_rate')
        pivot_rate.plot(ax=axes[1], kind='bar')
        axes[1].set_title('カテゴリ別変化率')
        axes[1].set_ylabel('変化率')
        
        plt.tight_layout()
        plt.savefig(output_path)
        
    def detect_anomalies(self, threshold: float = 0.3) -> List[Dict]:
        """異常な変化の検出"""
        df = self.analyze_growth_trend()
        
        anomalies = []
        for _, row in df.iterrows():
            if abs(row['change_rate']) > threshold:
                anomalies.append({
                    "timestamp": row['timestamp'],
                    "category": row['category'],
                    "change_rate": row['change_rate'],
                    "severity": "high" if abs(row['change_rate']) > 0.5 else "medium"
                })
                
        return anomalies