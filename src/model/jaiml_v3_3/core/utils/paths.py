# src/model/jaiml_v3_3/core/utils/paths.py
from pathlib import Path

def get_lexicon_path() -> Path:
    """
    統合辞書ファイルへの絶対パスを返す。
    プロジェクトルートからの相対位置を基準に解決する。
    
    Returns:
        Path: jaiml_lexicons.yaml への Path オブジェクト
    """
    # このファイルから4階層上がプロジェクトルート
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent.parent
    lexicon_path = project_root / "lexicons" / "jaiml_lexicons.yaml"
    
    if not lexicon_path.exists():
        raise FileNotFoundError(f"Lexicon file not found at: {lexicon_path}")
    
    return lexicon_path