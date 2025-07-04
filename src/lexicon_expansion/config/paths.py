# src/lexicon_expansion/config/paths.py
"""辞書拡張システム用の共通パス設定"""
from pathlib import Path

def get_project_root() -> Path:
    """プロジェクトルートを取得"""
    current_file = Path(__file__).resolve()
    # config/paths.py から3階層上がjaiml/
    return current_file.parent.parent.parent.parent

def get_lexicon_path() -> Path:
    """統合辞書ファイルへの絶対パスを返す"""
    lexicon_path = get_project_root() / "lexicons" / "jaiml_lexicons.yaml"
    if not lexicon_path.exists():
        raise FileNotFoundError(f"Lexicon file not found at: {lexicon_path}")
    return lexicon_path

def get_expansion_root() -> Path:
    """辞書拡張システムのルートパスを返す"""
    return get_project_root() / "src" / "lexicon_expansion"

def get_output_dir() -> Path:
    """出力ディレクトリのパスを返す"""
    output_dir = get_expansion_root() / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def get_corpus_dir() -> Path:
    """コーパスディレクトリのパスを返す"""
    corpus_dir = get_expansion_root() / "corpus"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    return corpus_dir

def get_config_path(filename: str) -> Path:
    """設定ファイルのパスを返す"""
    config_path = get_expansion_root() / "config" / filename
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    return config_path