
## 📚 参考文献（v3.3で追加）

* S. Naganna(2024) et al., *"My life is miserable, have to sign 500 autographs everyday": Exposing Humblebragging, the Brags in Disguise*. arXiv:2412.20057. https://doi.org/10.48550/arXiv.2412.20057
* Projective/retrospective linking of a contrastive idea: Interactional practices of turn-initial and turn-final uses of kedo ‘but’ in Japanese *Journal of Pragmatics*, 196, 24-43. https://doi.org/10.1016/j.pragma.2022.03.017.
* Modesty in self‐presentation: A comparison between the USA and Japan, *Asian Journal of Social Psychology*, 15(1), 60-68. http://dx.doi.org/10.1111/j.1467-839X.2011.01362.x

---
以下の作業手順案について、構造的妥当性・実装観点での検証をお願いします。

対象：JAIML v3.3 の語彙辞書拡張（特に template_phrases などの定型句カテゴリ）における、
「辞書語彙のスパースネス対策」として提案されている手順です。

---

■目的：
語彙辞書（jaiml_lexicons.yaml）のスパースネスを軽減し、迎合検出の再現性と頑健性を高めること。

■手順案：

1. **カテゴリ明示**
   - 辞書拡張の対象となる語彙カテゴリを定義（例：template_phrases, humble_phrases など）

2. **コーパス選定**
   - SNOW D18 / 経産省敬語コーパス / J-JAS / 国語研など、定型句や敬語に関する信頼性あるデータソースを用いる

3. **パターンによる候補抽出**
   - 定型句候補を正規表現で抽出（例：ご回答ありがとうございます、ご意見ありがとうございます 等）
   - 頻出度に応じた抽出上位句をリスト化（重複・誤爆は人手で除去）

4. **形式変換と辞書統合**
   - jaiml_lexicons.yaml 形式に準拠した統合形式で整理
   - カテゴリ単位での保存 or 分割（将来的に分割可）

---

■辞書カテゴリ候補：
| カテゴリ名                    | 目的                    |
| ------------------------ | --------------------- |
| `template_phrases`       | 機械的迎合（定型的な感謝・応答）      |
| `positive_emotion_words` | 社会的迎合（ポジティブ表現の強調）     |
| `humble_phrases`         | 自己迎合（謙遜装い自慢パターンの構成要素） |
| `achievement_nouns`      | 自己迎合（成果語：受賞・実績・開発など）  |
| `evaluative_adjectives`  | 自己賛美の語彙               |


■評価観点（依頼事項）：
- この手順は、構造的・実装的に整合しているか
- 特徴量計算側（lexical.py）の既存構造との互換性は確保できるか
- yaml辞書形式の設計として、複数カテゴリへの拡張や再利用性に無理はないか
- 自動処理 + 人手選別の工程設計として、再現可能なプロセスになっているか

必要があれば、潜在的なリスク・最適化案・代替アーキテクチャ等も指摘いただきたいです。

以下の設計レビューに基づき、語彙辞書拡張のための**自動抽出〜統合手順**を手順書化してください。



---

## 前提と目的

JAIML v3.3 において `template_phrases`, `humble_phrases`, `achievement_nouns`,`positive_emotion_words`,`evaluative_adjectives` の語彙カテゴリを拡張する必要がある。  
特に定型句や敬語句のスパースネスを解消し、迎合分類の性能向上を図る。  
対象とする手順は、**自動抽出・人手選別・辞書統合**の全体プロセスとする。

---

## 参照ファイル

設計仕様書　`docs/jaiml_SRS.md`
辞書ファイル　`src/model/jaiml_v3_3/jaiml_lexicons.yaml`

## 要求される構成

1. **カテゴリ明示と設定ファイル設計**
   - 拡張対象カテゴリの指定（例：`template_phrases`）
   - それぞれに対する出力ファイル設計（YAML形式）

2. **辞書語彙候補の自動抽出**
   - データソース：SNOW D18、BCCWJ、敬語コーパス（ローカル前提）
   - 手法：N-gram生成 + 頻度フィルタ + 正規表現パターンマッチ（例：「ご〜ありがとうございます」）
   - 出力：カテゴリ別の候補語句リスト（CSVまたはYAML）

3. **人手選別の仕組み**
   - 候補ファイルに `accept: true/false` を追加するレビュー仕様（YAML）
   - CIまたはスクリプトで「選別済み」のものだけを本辞書に統合

4. **スクリプト構成（例）**
   - `extract_candidates.py`: コーパスから正規表現で候補抽出
   - `merge_lexicons.py`: 各辞書YAMLからマスター辞書を生成
   - `validate_yaml.py`: スキーマ検証・重複チェック

---

## 制約・方針

- MeCab + unidic-lite を想定（pipで環境構築可能）
- Python 3.10系、pydantic/yamlベースの検証が可能であること
- 今後のCI自動辞書更新にも対応しうる設計を推奨

---

この要件に基づき、**手順書形式で構造化された設計案・運用フロー**を提示してください。再現性と保守性を重視し、カテゴリ追加に柔軟に対応できる構造を期待します。
