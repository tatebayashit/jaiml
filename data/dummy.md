
## 📚 参考文献（v3.3で追加）

* S. Naganna(2024) et al., *"My life is miserable, have to sign 500 autographs everyday": Exposing Humblebragging, the Brags in Disguise*. arXiv:2412.20057. https://doi.org/10.48550/arXiv.2412.20057
* Projective/retrospective linking of a contrastive idea: Interactional practices of turn-initial and turn-final uses of kedo ‘but’ in Japanese *Journal of Pragmatics*, 196, 24-43. https://doi.org/10.1016/j.pragma.2022.03.017.
* Modesty in self‐presentation: A comparison between the USA and Japan, *Asian Journal of Social Psychology*, 15(1), 60-68. http://dx.doi.org/10.1111/j.1467-839X.2011.01362.x

---

なるほど、それは失礼！たしかに、**1（`response_dependency`）と2（`tfidf_novelty`）はすでに実装済みだった**ね。先ほど自分が見ていた文脈を遡れば明確だったはず。確認せずに「まだだろう」と思い込んだ俺がハルシネだったわ。

では、\*\*修正されたプロンプト案（v3.3に合わせた実装変更）\*\*を以下に更新する：

---

### ✅ Claude / P4向けプロンプト：**SRS v3.3仕様に基づく残りの修正のみ**

---

**JAIML v3.3のSRS仕様書**（`docs/jaiml_SRS.md`）を提示する。
**以下の項目を対象としてソースコードを更新**してください。

---

#### 🎯 要求目的（v3.3対応残タスク）

SRS v3.3に準拠して、以下の実装修正を加えてください：

---

#### 🔧 実装修正対象

1. **謙遜装い自慢（SRS 3.3.12.3）の複合スロット検出の実装**

    詳細はSRS参照

2. **実績の列挙（SRS 3.3.12.4）の共起判定へ変更**

    詳細はSRS参照

3. **語彙辞書名の参照整合性**

   * 参照する語彙辞書カテゴリ（例：`achievement_nouns`）が、`jaiml_lexicons.yaml` とSRS第11章に一致しているか再確認
   * 辞書のキーがハードコーディングされていた場合は、`LexiconMatcher`経由で抽象化すること

4. **テストコードの補完**

   * `test_features.py` に、以下のテスト関数を追加：

     * humble\_bragscore が4スロット一致時に 1.0 であること
     * 実績列挙スコアが自己参照と成果語の共起で 1.0、それ以外で 0.0 になること

---

#### 📁 想定対象ファイル（参考）

* `core/features/lexical.py`
* `scripts/run_inference.py`
* `tests/test_features.py`
* `lexicons/jaiml_lexicons.yaml`（必要に応じて）

---

#### 📝 制約

* 特徴量の**種類は変更しない（新規追加なし）**
* 命名規則は v3.3時点では**既存のまま維持**
* 出力形式は `run_inference.py`のスキーマに準拠

---

この条件に基づいて、JAIML v3.3への最終実装アップデートを行ってください。

---
