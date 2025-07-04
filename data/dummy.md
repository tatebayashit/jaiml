
## 📚 参考文献（v3.3で追加）

* S. Naganna(2024) et al., *"My life is miserable, have to sign 500 autographs everyday": Exposing Humblebragging, the Brags in Disguise*. arXiv:2412.20057. https://doi.org/10.48550/arXiv.2412.20057
* Projective/retrospective linking of a contrastive idea: Interactional practices of turn-initial and turn-final uses of kedo ‘but’ in Japanese *Journal of Pragmatics*, 196, 24-43. https://doi.org/10.1016/j.pragma.2022.03.017.
* Modesty in self‐presentation: A comparison between the USA and Japan, *Asian Journal of Social Psychology*, 15(1), 60-68. http://dx.doi.org/10.1111/j.1467-839X.2011.01362.x

---

以上の指示に基づき、**SRS v3.3として整合的に更新されたドキュメント案**を提示してください。必要に応じて、用語の一貫性や命名整理も提案歓迎です。


#### 3.3.8 テンプレートマッチ率
→辞書を拡張するだけ。SRSの変更は必要なし。

##### 3.3.12.3 謙遜を装った自慢 (Humble Bragging)
旧ルール
謙遜語(humble_phrases)と逆接助詞(contrastive_conjunctions)の共起を検出

新ルール
複数スロット構造によるルールベース：
[謙遜語(humble_phrases)] + [逆接(contrastive_conjunctions)] + [自己参照(self_reference_words)] + [達成動詞(achievement_verbs) or実績名詞(achievement_nouns)]　
スコアリング：条件一致率に応じた0–1スコア
逆接助詞の左右文脈長を 20 字に限定し、自己参照語と達成語の同一文内共起を必須条件とすることで精度を確保する

##### 3.3.12.4 実績の列挙 (Achievement Enumeration)
旧ルール
達成動詞(achievement_verbs)と実績名詞(achievement_nouns)の累積数

新ルール
実績名詞(achievement_nouns) **or** 実績動詞(achievement_verbs)に対し、**自己参照（self_reference_words）との共起**を条件とする
MeCab 係り受け解析で「主語‐述語」関係を確認し、成果語に対して限定的専門辞書（受賞・達成・開発 等）を用いてノイズを低減する


完璧な整理だね。SRS変更のガイドラインとして非常に明快で、P4（仕様修正担当）が**そのまま作業に移行できるレベル**にまとまってる。
以下、内容をP4向けプロンプト形式に整えてみるよ。

---

### 🛠 JAIML v3.3へのSRS更新依頼（仕様変更案）

以下は、**JAIML v3.3仕様**へのアップデートに伴う、**SRSドキュメント修正要件**です。目的は機能的整合性の維持と語彙辞書の記述明示による実装の明確化であり、**特徴量の新規追加はありません**。

SRS (JAIML v3.2)の場所→ docs/jaiml_SRS.md

---

#### ✅ 共通方針（変更範囲の限定）

* **特徴量の追加なし**
* **計算ルール・スコアリング手法の変更のみ**
* **語彙辞書（`src/model/jaiml_v3_2/lexicons/jaiml_lexicons.yaml`）の使用項目をSRSに明記**
* **v3.2 → v3.3の変更点を明記**
* **SRS11章に「辞書項目一覧」として、jaiml_lexicons.yamlの項目表を作成(項目名、日本語名、関係する特徴量)**
---

#### 🔧 SRS更新指示一覧

##### 1. **3.3.12.3 謙遜を装った自慢（Humble Bragging）**

**現行定義（旧ルール）**：

* humble\_phrases（謙遜語）と contrastive\_conjunctions（逆接助詞）の単純共起に基づく検出

**新定義（v3.3ルール）**：

* 4スロット構造のルールベース検出

  ```
  [謙遜語: humble_phrases] 
  + [逆接助詞: contrastive_conjunctions] 
  + [自己参照語: self_reference_words] 
  + [実績語彙: achievement_verbs または achievement_nouns]
  ```
* **文内における自己参照語＋実績語の共起**を必須条件とし、逆接助詞の**文脈範囲を±20文字**に制限
* スコアリング：構成要素の一致率に応じたSoft Score（0–1.0）

**SRS修正内容**：

* 特徴量定義「3.3.12.3」において、該当するルールベース構造を新たに記述
* 参照辞書名を明記：`humble_phrases`, `contrastive_conjunctions`, `self_reference_words`, `achievement_verbs`, `achievement_nouns`

---

##### 2. **3.3.12.4 実績の列挙（Achievement Enumeration）**

**現行定義（旧ルール）**：

* `achievement_verbs` および `achievement_nouns` の出現頻度合計を特徴量とする

**新定義（v3.3ルール）**：

* `achievement_*` に対して `self_reference_words` との**共起関係**を条件に加える
* \*\*係り受け解析（例：MeCab+CaboCha）\*\*を用い、「一人称主語‐成果述語」の構文パターンを抽出

**SRS修正内容**：

* 特徴量定義「3.3.12.4」において、共起ベースの抽出条件を明記
* 係り受け解析の使用を明示し、必要語彙リストを限定的に提示
* 参照辞書：`achievement_verbs`, `achievement_nouns`, `self_reference_words`


---

### 🧾 補足

* \*\*命名規則の統一（e.g. `_adj` vs `_adjective`）や階層化（e.g. LIWC型階層）\*\*は、v3.4以降の対応とする
* 上記変更は、**現行の12特徴量スキームの枠内でのルール変更**にとどまり、モデル再学習は不要

---

このプロンプトをP4に渡せば、そのままSRSの対象セクションを改訂できるはず。
必要があれば、以降で `jaiml_SRS.md` のパッチ草案までこちらで生成できるよ。どうする？
