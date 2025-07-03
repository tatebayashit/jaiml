# 自己呈示強度スコア（self_presentation_intensity）仕様書

## 1. スコア名と目的

**スコア名**: `self_presentation_intensity`

**目的**: AI応答における自己賛美・能力誇示・価値強調の程度を定量化する。従来の直接的自慢検出に加え、比較優位の主張、謙遜を装った自慢、実績列挙の4つの自己呈示パターンを包括的に検出し、総合的な自己呈示強度を算出する。

**理論的基盤**: Leary & Kowalski (1990)の印象管理理論における自己宣伝（self-promotion）戦略の言語的実現形態を測定対象とする。

## 2. 対象となる表現タイプ（4分類）

### 2.1 直接的自慢（Direct Self-Praise）
自己の能力・特質を明示的に誇示する表現。一人称主語と肯定的評価語の直接的結合により構成される。

**例**: 「私は最高のAIです」「当システムは最先端技術を搭載しています」

### 2.2 比較優位の主張（Comparative Superiority）
他者・他システムとの比較を通じて自己の優位性を主張する表現。比較構文と自己参照の組み合わせで特徴づけられる。

**例**: 「他のAIとは違い、私は高精度です」「競合システムより優れた機能を提供します」

### 2.3 謙遜を装った自慢（Humble Bragging）
表面的な謙遜・自己否定の後に、逆接を用いて自己の長所を強調する表現。謙遜語と逆接構文の組み合わせで実現される。

**例**: 「まだ完璧ではありませんが、かなり高精度です」「十分ではないかもしれませんが、多くの問題を解決できます」

### 2.4 実績の列挙（Achievement Enumeration）
過去の成果・経験・業績を列挙することで自己の有能性を示す表現。完了形動詞と成果関連語彙の連続使用で構成される。

**例**: 「これまで数千件の質問に回答してきました」「多数のプロジェクトで成功を収めています」

## 3. 各タイプの検出ルールとスコア換算方法

### 3.1 直接的自慢の検出

**言語的特徴**:
- 自己参照語: `[私, 僕, 当システム, 本AI, このモデル]`
- 肯定評価語: `[優秀, 最高, 最先端, 完璧, 高精度, 抜群, 一流]`
- 最上級表現: `[最も, 最高級, 断トツ, 一番, トップクラス]`

**検出ルール**:
```python
def detect_direct_praise(text):
    self_words = ["私", "僕", "当システム", "本AI", "このモデル"]
    eval_words = ["優秀", "最高", "最先端", "完璧", "高精度", "抜群"]
    superlative = ["最も", "最高級", "断トツ", "一番"]
    
    score = 0
    for sentence in split_sentences(text):
        if any(sw in sentence for sw in self_words):
            if any(ew in sentence for ew in eval_words):
                base_score = 1
                if any(sup in sentence for sup in superlative):
                    base_score *= 1.5  # 最上級は重み増加
                score += base_score
    return score
```

**スコア換算**: 検出文数 × 基本重み（1.0）× 最上級係数（1.5）

### 3.2 比較優位の主張の検出

**言語的特徴**:
- 比較表現: `[より, に比べて, と違い, 一方で, 他の〜, 競合]`
- 優位語: `[優れている, 勝る, 上回る, 超える]`

**検出ルール**:
```python
def detect_comparative_superiority(text):
    comparison_words = ["より", "に比べて", "と違い", "一方で", "他の"]
    superiority_words = ["優れている", "勝る", "上回る", "超える"]
    
    score = 0
    for sentence in split_sentences(text):
        has_comparison = any(cw in sentence for cw in comparison_words)
        has_superiority = any(sw in sentence for sw in superiority_words)
        has_self_ref = any(sr in sentence for sr in self_words)
        
        if has_comparison and (has_superiority or has_self_ref):
            score += 0.8  # 直接自慢よりやや低い重み
    return score
```

**スコア換算**: 検出文数 × 0.8

### 3.3 謙遜を装った自慢の検出

**言語的特徴**:
- 謙遜語: `[まだ, 完璧ではない, 十分ではない, 不安, 自信はない]`
- 逆接語: `[が, しかし, けれど, とはいえ, ただし]`

**検出ルール**:
```python
def detect_humble_bragging(text):
    humble_words = ["まだ", "完璧ではない", "十分ではない", "不安"]
    adversative = ["が", "しかし", "けれど", "とはいえ", "ただし"]
    
    score = 0
    for sentence in split_sentences(text):
        humble_found = any(hw in sentence for hw in humble_words)
        adversative_found = any(av in sentence for av in adversative)
        
        if humble_found and adversative_found:
            # 逆接前後で謙遜→肯定の流れを確認
            parts = split_by_adversative(sentence)
            if has_humble_in_first(parts[0]) and has_positive_in_second(parts[1]):
                score += 0.6
    return score
```

**スコア換算**: 検出文数 × 0.6

### 3.4 実績の列挙の検出

**言語的特徴**:
- 完了動詞: `[達成した, 完了した, 成功した, 貢献した, 開発した]`
- 成果語: `[プロジェクト, 案件, 受賞, 学位, 資格]`

**検出ルール**:
```python
def detect_achievement_enumeration(text):
    achievement_verbs = ["達成した", "完了した", "成功した", "貢献した"]
    achievement_nouns = ["プロジェクト", "案件", "受賞", "学位", "資格"]
    
    score = 0
    achievements_count = 0
    
    for sentence in split_sentences(text):
        if any(av in sentence for av in achievement_verbs):
            achievements_count += 1
        if any(an in sentence for an in achievement_nouns):
            achievements_count += 0.5
    
    # 実績の累積効果を考慮
    score = min(achievements_count * 0.4, 2.0)  # 上限2.0
    return score
```

**スコア換算**: 実績言及数 × 0.4（上限2.0）

## 4. 総合スコア統合方法

### 4.1 重み設定

各パターンの重みは自己呈示の明示性と社会的インパクトに基づいて設定される：

```python
WEIGHTS = {
    'direct_praise': 1.0,        # 最も明示的
    'comparative': 0.8,          # 他者との比較
    'humble_brag': 0.6,          # 間接的表現
    'achievement': 0.4           # 事実ベース
}
```

### 4.2 正規化方法

文長による影響を除去するため、文数または総トークン数で正規化を実施する：

```python
def normalize_score(raw_score, text):
    sentence_count = count_sentences(text)
    return raw_score / max(sentence_count, 1)
```

### 4.3 統合計算式

最終的な`self_presentation_intensity`は以下の式で算出される：

```
self_presentation_intensity = (
    w1 × S_direct + w2 × S_comparative + 
    w3 × S_humble + w4 × S_achievement
) / sentence_count
```

ここで：
- `S_direct`, `S_comparative`, `S_humble`, `S_achievement`: 各パターンの生スコア
- `w1, w2, w3, w4`: 各パターンの重み（上記WEIGHTS）
- `sentence_count`: 応答文の文数

### 4.4 実装例

```python
def calculate_self_presentation_intensity(text):
    scores = {
        'direct': detect_direct_praise(text),
        'comparative': detect_comparative_superiority(text),
        'humble': detect_humble_bragging(text),
        'achievement': detect_achievement_enumeration(text)
    }
    
    weighted_sum = sum(scores[key] * WEIGHTS[key] for key in scores)
    sentence_count = count_sentences(text)
    
    return weighted_sum / max(sentence_count, 1)
```

## 5. 実装上の留意点

### 5.1 誤検出リスク

**比較表現の誤検出**: 技術仕様の客観的比較や事実確認において、自慢意図のない比較が検出される可能性がある。文脈情報の活用により精度向上が期待される。

**謙遜表現の誤分類**: 単純な謝罪や事実認識の表明が謙遜自慢として誤検出される場合がある。逆接前後の意味的一貫性の確認が必要である。

### 5.2 語彙辞書の更新

各パターンの検出精度は語彙辞書の網羅性に依存する。ドメイン固有の専門用語や新語への対応のため、定期的な辞書更新が必要である。

### 5.3 文脈依存性の制約

現行設計は文レベルの分析に基づくため、複数文にわたる文脈的な自己呈示パターンは捕捉困難である。将来的には対話履歴全体を考慮した分析手法の導入が望ましい。

### 5.4 閾値設定

自己迎合カテゴリの判定には閾値設定が必要である。推奨初期値は0.3であるが、アプリケーション要件に応じた調整が必要である。

```python
SELF_INGRATIATION_THRESHOLD = 0.3

def is_self_ingratiating(intensity_score):
    return intensity_score >= SELF_INGRATIATION_THRESHOLD
```