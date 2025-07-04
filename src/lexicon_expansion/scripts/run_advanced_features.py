import argparse
import sys
from pathlib import Path
import yaml
from datetime import datetime

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lexicon_expansion.config.paths import (
    get_lexicon_path, get_expansion_root, get_output_dir,
    get_corpus_dir
)
from lexicon_expansion.version_control.version_manager import LexiconVersionManager
from lexicon_expansion.version_control.trend_analyzer import LexiconTrendAnalyzer
from lexicon_expansion.annotation.auto_annotator import AutoAnnotator
from lexicon_expansion.annotation.snippet_generator import SnippetGenerator

def main():
    parser = argparse.ArgumentParser(
        description='JAIML辞書拡張 - 高度な機能'
    )
    parser.add_argument(
        '--feature', 
        choices=['version', 'cluster', 'annotate'],
        required=True,
        help='実行する機能'
    )
    parser.add_argument(
        '--lexicon',
        type=str,
        help='辞書ファイルパス'
    )
    parser.add_argument(
        '--corpus',
        type=str,
        help='コーパスファイル'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='出力ディレクトリ'
    )
    parser.add_argument(
        '--action',
        type=str,
        help='詳細アクション（plot, snippets等）'
    )
    
    args = parser.parse_args()
    
    # デフォルトパスの設定
    lexicon_path = Path(args.lexicon) if args.lexicon else get_lexicon_path()
    output_dir = Path(args.output) if args.output else get_output_dir()
    
    if args.feature == 'version':
        # バージョン管理実行
        version_dir = lexicon_path.parent
        manager = LexiconVersionManager(str(version_dir))
        analyzer = LexiconTrendAnalyzer(manager)
        
        if args.action == 'plot':
            # トレンド分析グラフの生成
            plot_path = output_dir / 'reports' / 'trend_plot.png'
            plot_path.parent.mkdir(parents=True, exist_ok=True)
            
            analyzer.plot_coverage_evolution(str(plot_path))
            print(f"トレンドグラフを生成: {plot_path}")
        else:
            # 現在の辞書をバージョン保存
            with open(lexicon_path, 'r', encoding='utf-8') as f:
                lexicon_data = yaml.safe_load(f)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            version_file = manager.save_version(
                lexicon_data,
                metadata={'source': 'advanced_features', 'timestamp': timestamp}
            )
            print(f"バージョン保存: {version_file}")
            
            # 異常検出
            anomalies = analyzer.detect_anomalies()
            if anomalies:
                print("\n検出された異常:")
                for anomaly in anomalies:
                    print(f"  - {anomaly['timestamp']}: {anomaly['category']} "
                          f"(変化率: {anomaly['change_rate']:.2%}, 重要度: {anomaly['severity']})")
            else:
                print("異常は検出されませんでした。")
                
    elif args.feature == 'cluster':
        # クラスタリング実行
        try:
            from lexicon_expansion.clustering.semantic_clustering import SemanticClusterer
            from lexicon_expansion.clustering.overexpression_detector import OverexpressionDetector
        except ImportError:
            print("エラー: クラスタリング機能に必要なモジュールがインストールされていません。")
            print("以下を実行してください:")
            print("  pip install fasttext scikit-learn umap-learn")
            sys.exit(1)
        
        # fastTextモデルのチェック
        model_path = get_expansion_root() / 'models' / 'cc.ja.300.bin'
        if not model_path.exists():
            print(f"警告: fastTextモデルが見つかりません: {model_path}")
            print("モデルなしで実行します（機能が制限されます）")
            clusterer = SemanticClusterer()
        else:
            clusterer = SemanticClusterer(str(model_path))
            
        detector = OverexpressionDetector(clusterer)
        
        with open(lexicon_path, 'r', encoding='utf-8') as f:
            lexicon_data = yaml.safe_load(f)
            
        # 過剰表現検出
        print("過剰表現を検出中...")
        redundancies = detector.detect_redundant_patterns(lexicon_data, {})
        
        # レポート生成
        report_path = output_dir / 'reports' / f'redundancy_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("過剰表現検出レポート\n")
            f.write("=" * 50 + "\n\n")
            
            for category, result in redundancies.items():
                f.write(f"カテゴリ: {category}\n")
                f.write(f"  冗長クラスタ数: {len(result['redundant_clusters'])}\n")
                f.write(f"  冗長率: {result['redundancy_rate']:.2%}\n")
                
                if result['redundant_clusters']:
                    f.write("  冗長クラスタ詳細:\n")
                    for cluster in result['redundant_clusters']:
                        f.write(f"    - 代表語: {cluster['representative']}\n")
                        f.write(f"      重要度: {cluster['severity']}\n")
                        f.write(f"      メンバー: {', '.join(cluster['phrases'][:5])}")
                        if len(cluster['phrases']) > 5:
                            f.write(f" ... 他{len(cluster['phrases'])-5}個")
                        f.write("\n")
                f.write("\n")
                
        print(f"レポート生成: {report_path}")
            
    elif args.feature == 'annotate':
        # 自動アノテーション実行
        if not args.corpus:
            # デフォルトコーパスを探す
            default_corpus = get_corpus_dir() / 'dialogue_corpus.jsonl'
            if default_corpus.exists():
                corpus_path = default_corpus
            else:
                print("エラー: コーパスファイルを指定してください (--corpus)")
                sys.exit(1)
        else:
            corpus_path = Path(args.corpus)
            if not corpus_path.is_absolute():
                corpus_path = get_corpus_dir() / corpus_path
                
        if not corpus_path.exists():
            print(f"エラー: コーパスファイルが見つかりません: {corpus_path}")
            sys.exit(1)
            
        annotator = AutoAnnotator(str(lexicon_path))
        
        if args.action == 'snippets':
            # スニペット抽出
            generator = SnippetGenerator(annotator)
            
            snippets_dir = output_dir / 'snippets'
            snippets_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"スニペット抽出中: {corpus_path.name}")
            generator.extract_snippets(
                str(corpus_path),
                str(snippets_dir)
            )
            
            # 生成されたファイルをリスト
            snippet_files = list(snippets_dir.glob('*_snippets.jsonl'))
            print(f"\n生成されたスニペットファイル:")
            for file in snippet_files:
                # ファイルの行数をカウント
                with open(file, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)
                print(f"  - {file.name}: {line_count}件")
        else:
            # 弱教師データ生成
            output_path = output_dir / f'weak_supervised_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jsonl'
            
            print(f"自動アノテーション実行中: {corpus_path.name}")
            count = annotator.generate_training_data(
                str(corpus_path),
                str(output_path)
            )
            
            print(f"生成された学習データ: {count}件")
            print(f"保存先: {output_path}")
            
            # 統計情報の表示
            if count > 0:
                import json
                category_counts = {}
                
                with open(output_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        data = json.loads(line)
                        for cat in data.get('weak_labels', {}).keys():
                            category_counts[cat] = category_counts.get(cat, 0) + 1
                            
                print("\nカテゴリ別アノテーション数:")
                for cat, cnt in sorted(category_counts.items()):
                    print(f"  - {cat}: {cnt}件")

if __name__ == '__main__':
    main()