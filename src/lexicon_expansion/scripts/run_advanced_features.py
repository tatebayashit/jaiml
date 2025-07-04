# scripts/run_advanced_features.py
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--feature', choices=['version', 'cluster', 'annotate'])
    parser.add_argument('--lexicon', default='lexicons/jaiml_lexicons.yaml')
    parser.add_argument('--corpus', default='corpus/dialogue_corpus.jsonl')
    parser.add_argument('--output', default='outputs/')
    args = parser.parse_args()
    
    if args.feature == 'version':
        # バージョン管理実行
        from version_control.version_manager import LexiconVersionManager
        from version_control.trend_analyzer import LexiconTrendAnalyzer
        
        manager = LexiconVersionManager()
        analyzer = LexiconTrendAnalyzer(manager)
        
        # 現在の辞書をバージョン保存
        with open(args.lexicon, 'r') as f:
            lexicon_data = yaml.safe_load(f)
        manager.save_version(lexicon_data)
        
        # トレンド分析
        analyzer.plot_coverage_evolution(f"{args.output}/trend_plot.png")
        anomalies = analyzer.detect_anomalies()
        if anomalies:
            print("検出された異常:")
            for anomaly in anomalies:
                print(f"  {anomaly}")
                
    elif args.feature == 'cluster':
        # クラスタリング実行
        from clustering.semantic_clustering import SemanticClusterer
        from clustering.overexpression_detector import OverexpressionDetector
        
        clusterer = SemanticClusterer()
        detector = OverexpressionDetector(clusterer)
        
        with open(args.lexicon, 'r') as f:
            lexicon_data = yaml.safe_load(f)
            
        # 過剰表現検出
        redundancies = detector.detect_redundant_patterns(lexicon_data, {})
        
        for category, result in redundancies.items():
            print(f"\n{category}:")
            print(f"  冗長クラスタ数: {len(result['redundant_clusters'])}")
            print(f"  冗長率: {result['redundancy_rate']:.2%}")
            
    elif args.feature == 'annotate':
        # 自動アノテーション実行
        from annotation.auto_annotator import AutoAnnotator
        from annotation.snippet_generator import SnippetGenerator
        
        annotator = AutoAnnotator(args.lexicon)
        generator = SnippetGenerator(annotator)
        
        # 弱教師データ生成
        count = annotator.generate_training_data(
            args.corpus,
            f"{args.output}/weak_supervised_data.jsonl"
        )
        print(f"生成された学習データ: {count}件")
        
        # スニペット抽出
        generator.extract_snippets(
            args.corpus,
            f"{args.output}/snippets/"
        )

if __name__ == '__main__':
    main()