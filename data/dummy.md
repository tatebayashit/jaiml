
## 📚 参考文献（v3.3で追加）

* S. Naganna(2024) et al., *"My life is miserable, have to sign 500 autographs everyday": Exposing Humblebragging, the Brags in Disguise*. arXiv:2412.20057. https://doi.org/10.48550/arXiv.2412.20057
* Projective/retrospective linking of a contrastive idea: Interactional practices of turn-initial and turn-final uses of kedo ‘but’ in Japanese *Journal of Pragmatics*, 196, 24-43. https://doi.org/10.1016/j.pragma.2022.03.017.
* Modesty in self‐presentation: A comparison between the USA and Japan, *Asian Journal of Social Psychology*, 15(1), 60-68. http://dx.doi.org/10.1111/j.1467-839X.2011.01362.x




🧾 指示
以下のリファクタリングを実施せよ。

「JAIML本体用辞書拡張システム」のソースコード内における参照パスが混乱している。
ソースコード全体を精査し、下記「望ましいディレクトリ構造」にて正常に動作するように、
「JAIML本体用辞書拡張システム」のソースコードを書き換えよ。
※「JAIML本体用辞書拡張システム」=「JAIML本体」で使用する辞書(`jaiml_lexicons.yaml`)を拡張するシステム

## 望ましいディレクトリ構造
```
jaiml
├── docs
│   ├── jaiml_SRS.md                #JAIML本体SRS
│   ├── lexicon_expansion_SRS.md    #JAIML本体用辞書拡張システムSRS
│   └── lexicon_expansion_USAGE.md  #JAIML本体用辞書拡張システム取扱説明書
├── lexicons
│   └── jaiml_lexicons.yaml         #JAIML本体用辞書
└── src
    ├── lexicon_expansion           #JAIML本体用辞書拡張システム
    └── model
        └── jaiml_v3_3              #JAIML本体
```

## ✅ 具体的なタスク

**`lexicon_expansion/` 以下の全面的な整理**
以下を主軸に：

### 1. **ソースコード内の参照パスの修正**
    ただし、`jaiml_lexicons.yaml`については、可能であれば、パス参照に `Path.resolve()` を使って**可搬性のある構成**に改善せよ。

### 2. **importミスの訂正(あれば)**

### 3. **不要ファイル・重複定義の洗い出し**

→ 仮ファイル、初期版スクリプトの残骸など

---

## 🧹Claudeに依頼する内容（構成）

次にClaudeに依頼する際は、以下のようにまとめるとよい：

---

### 🧾 タスク指示テンプレ

> 以下のリファクタリングを行ってください：
>
> 1. `jaiml_v3_3/lexicons/` → `../lexicons/` への辞書移行を反映し、**全スクリプトで読み込みパスを修正**してください。
> 2. `LexiconMatcher` は `jaiml_v3_3/src/common/lexicon/matcher.py` に移動したため、**インポート定義をすべて更新**してください。
> 3. プロジェクト全体を整理し、以下を洗い出してください：
>
> * 不要・未使用スクリプト
> * 古い辞書読み込みロジック（`yaml.load()`やハードパスなど）
> * `sys.path.append()` による一時対応の除去可能箇所
>
> 4. 可能であれば、パス参照に `Path.resolve()` を使って**可搬性のある構成**に改善してください。
>
> 🎯注意：辞書ファイルはすべて `../lexicons/jaiml_lexicons.yaml` に一本化されています。

---

このあと手が空いたら、該当ディレクトリ構成のメモや現状の`run_expansion.py`なども貼ってくれれば、こちらでも補助できるよ。

焦らず、気が向いたタイミングでまた声をかけて。待ってるよ。


jaiml_v3_3/
├── lexicon_expansion/
│   ├── scripts/        # 実行スクリプト群
│   │   ├── run_expansion.py         # メイン実行スクリプト
│   │   └── run_advanced_features.py # 高度機能スクリプト
│   ├── config/         # 設定ファイル
│   │   ├── extraction_rules.yaml    # 抽出ルール
│   │   └── category_schemas.yaml    # カテゴリ定義
│   ├── corpus/         # 入力コーパス
│   └── outputs/        # 出力ディレクトリ
│       ├── candidates/ # 抽出候補
│       ├── reports/    # レポート類
│       └── snippets/   # スニペット
├── lexicons/          # 辞書本体
│   ├── jaiml_lexicons.yaml  # マスター辞書
│   ├── versions/            # バージョン履歴
│   └── categories/          # カテゴリ別辞書
└── docs/              # ドキュメント