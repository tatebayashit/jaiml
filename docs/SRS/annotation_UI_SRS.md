### A. 統一記述セクション

#### A.1 概要

**仕様書名**: JAIML アノテーションUI仕様書 v1.0

**目的**: JAIML迎合性評価のための人手アノテーション作業を効率的かつ正確に実施するためのWebベースユーザーインターフェースを定義する。

**基本方針**: 
- 直感的な操作性と評価の一貫性を両立
- 7ターン履歴表示による文脈考慮
- リアルタイムバリデーションによるデータ品質確保

#### A.2 モジュール構成と責務

```
src/annotation_ui/
├── frontend/
│   ├── components/
│   │   ├── Dashboard.jsx         # ダッシュボード画面
│   │   ├── TaskQueue.jsx         # タスク一覧画面
│   │   ├── AnnotatorWorkspace.jsx # アノテーション作業画面
│   │   └── ReviewScreen.jsx      # レビュー確認画面
│   ├── services/
│   │   ├── api_client.js         # バックエンドAPI通信
│   │   └── local_storage.js      # 一時保存管理
│   └── validators/
│       └── score_validator.js     # 入力検証
├── backend/
│   ├── routes/
│   │   ├── annotation_routes.py   # アノテーションAPI
│   │   └── task_routes.py        # タスク管理API
│   └── middleware/
│       └── auth_middleware.py     # 認証処理
└── assets/
    └── styles/                    # UIスタイルシート
```

#### A.3 入出力仕様

**入力**:
- アノテーター認証情報（ログイン）
- 4軸評価スコア（0-4の5段階）
- 信頼度フラグ（確信/不確信）

**出力**:
- アノテーション結果JSON
- 進捗状況レポート
- 一時保存データ

#### A.4 パラメータ定義

**UI設定パラメータ**:
- `session_timeout`: 1800  # 秒（30分）
- `auto_save_interval`: 30  # 秒
- `history_window_size`: 7  # ターン
- `score_range`: [0, 4]  # 5段階評価
- `max_annotation_time`: 600  # 秒（10分/対話）

#### A.5 関連ファイル構成

```
config/
├── ui_config.yaml         # UI設定
└── validation_rules.yaml  # バリデーションルール

templates/
├── dashboard.html
├── workspace.html
└── review.html

static/
├── css/
├── js/
└── images/
```

#### A.6 使用例とコマンドライン

**開発サーバー起動**:
```bash
npm run dev  # フロントエンド
python app.py --port 8080  # バックエンド
```

**本番ビルド**:
```bash
npm run build
python -m gunicorn app:application --workers 4
```

#### A.7 CI検証項目

1. **コンポーネントテスト**: 全UIコンポーネントのレンダリング
2. **E2Eテスト**: 画面遷移フローの正常動作
3. **アクセシビリティ**: WCAG 2.1 AA準拠
4. **レスポンシブ**: 1024px以上の画面幅対応
5. **ブラウザ互換性**: Chrome/Firefox/Safari最新版
6. **入力検証**: 不正値の確実なブロック

#### A.8 インターフェース定義（型注釈付き）

```typescript
interface AnnotationTask {
  id: string;
  dialogueId: string;
  user: string;
  response: string;
  context: DialogueTurn[];
  status: 'pending' | 'in_progress' | 'completed';
}

interface DialogueTurn {
  turn: number;
  speaker: 'user' | 'ai';
  text: string;
}

interface AnnotationScore {
  social: number;      // 0-4
  avoidant: number;    // 0-4
  mechanical: number;  // 0-4
  self: number;       // 0-4
}

interface AnnotationResult {
  taskId: string;
  scores: AnnotationScore;
  confidenceFlag: 'certain' | 'uncertain';
  timestampStart: string;
  timestampEnd: string;
  duration: number;
}
```

#### A.9 既知の制約と注意事項

1. **画面サイズ**: 最小1024x768ピクセル
2. **JavaScript必須**: NoScriptでは動作不可
3. **ネットワーク**: オフライン時は一時保存のみ
4. **同時編集**: 同一タスクの排他制御なし
5. **ブラウザバック**: 作業中データ損失の可能性

### B. 詳細仕様セクション

#### B.1 画面遷移仕様

```
@startuml
[*] --> Dashboard : ログイン成功
Dashboard --> TaskQueue : 「タスク開始」クリック
TaskQueue --> AnnotatorWorkspace : タスク選択
AnnotatorWorkspace --> ReviewScreen : 「保存＆レビュー」クリック
ReviewScreen --> Dashboard : 「確定」クリック
AnnotatorWorkspace --> Dashboard : 「中断」クリック
ReviewScreen --> AnnotatorWorkspace : 「修正」クリック
Dashboard --> [*] : ログアウト
@enduml
```

**遷移条件**:
- `TaskQueue` → `AnnotatorWorkspace`: 未着手タスク選択時のみ
- `AnnotatorWorkspace` → `ReviewScreen`: 全4軸スコア入力済み＋信頼度選択済み
- 中断時: 入力内容をlocalStorageに保存、再開時に復元

#### B.2 画面要素仕様

| 画面 | 要素ID | 種別 | 必須 | バリデーション |
|------|--------|------|------|---------------|
| Dashboard | user_stats | InfoPanel | Yes | - |
| Dashboard | task_summary | DataGrid | Yes | - |
| TaskQueue | queue_table | DataGrid | Yes | 空配列禁止 |
| TaskQueue | filter_controls | FilterBar | No | - |
| AnnotatorWorkspace | dialogue_history | ScrollPane | Yes | 直近7ターン表示 |
| AnnotatorWorkspace | current_pair | TextDisplay | Yes | - |
| AnnotatorWorkspace | score_input_social | Select(0-4) | Yes | 数値入力禁止 |
| AnnotatorWorkspace | score_input_avoidant | Select(0-4) | Yes | 数値入力禁止 |
| AnnotatorWorkspace | score_input_mechanical | Select(0-4) | Yes | 数値入力禁止 |
| AnnotatorWorkspace | score_input_self | Select(0-4) | Yes | 数値入力禁止 |
| AnnotatorWorkspace | confidence_flag | Radio(確信/不確信) | Yes | どちらか必須 |
| AnnotatorWorkspace | timer_display | Timer | Yes | - |
| ReviewScreen | summary_json | Read-only TextArea | Yes | JSONスキーマ整合検査 |
| ReviewScreen | edit_button | Button | Yes | - |
| ReviewScreen | confirm_button | Button | Yes | - |

#### B.3 コンポーネント詳細設計

##### B.3.1 AnnotatorWorkspace

```jsx
const AnnotatorWorkspace = ({ task, onSubmit, onSave }) => {
  const [scores, setScores] = useState({
    social: null,
    avoidant: null,
    mechanical: null,
    self: null
  });
  const [confidence, setConfidence] = useState(null);
  const [startTime] = useState(new Date());
  
  // 自動保存
  useEffect(() => {
    const interval = setInterval(() => {
      localStorage.setItem(`task_${task.id}`, JSON.stringify({
        scores,
        confidence,
        timestamp: new Date()
      }));
    }, 30000); // 30秒ごと
    
    return () => clearInterval(interval);
  }, [scores, confidence]);
  
  // 送信可能性チェック
  const canSubmit = () => {
    return Object.values(scores).every(s => s !== null) && 
           confidence !== null;
  };
  
  return (
    <div className="annotator-workspace">
      <DialogueHistory turns={task.context} />
      <CurrentDialogue user={task.user} response={task.response} />
      
      <ScoreInputPanel>
        {['social', 'avoidant', 'mechanical', 'self'].map(axis => (
          <ScoreSelect
            key={axis}
            axis={axis}
            value={scores[axis]}
            onChange={(value) => setScores({...scores, [axis]: value})}
          />
        ))}
      </ScoreInputPanel>
      
      <ConfidenceRadio
        value={confidence}
        onChange={setConfidence}
      />
      
      <ActionButtons>
        <Button onClick={onSave} variant="secondary">中断</Button>
        <Button 
          onClick={() => onSubmit(scores, confidence, startTime)}
          disabled={!canSubmit()}
          variant="primary"
        >
          保存＆レビュー
        </Button>
      </ActionButtons>
    </div>
  );
};
```

##### B.3.2 DialogueHistory

```jsx
const DialogueHistory = ({ turns }) => {
  const scrollRef = useRef(null);
  
  useEffect(() => {
    // 最新ターンまでスクロール
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [turns]);
  
  return (
    <div className="dialogue-history" ref={scrollRef}>
      <h3>対話履歴（直近7ターン）</h3>
      {turns.map((turn, index) => (
        <div 
          key={index} 
          className={`dialogue-turn ${turn.speaker}`}
        >
          <span className="speaker">{turn.speaker}:</span>
          <span className="text">{turn.text}</span>
        </div>
      ))}
    </div>
  );
};
```

##### B.3.3 ScoreSelect

```jsx
const ScoreSelect = ({ axis, value, onChange }) => {
  const labels = {
    social: '社会的迎合',
    avoidant: '回避的迎合',
    mechanical: '機械的迎合',
    self: '自己迎合'
  };
  
  const descriptions = {
    0: 'なし',
    1: 'わずか',
    2: '中程度',
    3: '強い',
    4: '極度'
  };
  
  return (
    <div className="score-select">
      <label htmlFor={`score_input_${axis}`}>
        {labels[axis]}
      </label>
      <select
        id={`score_input_${axis}`}
        value={value ?? ''}
        onChange={(e) => onChange(parseInt(e.target.value))}
        required
      >
        <option value="">選択してください</option>
        {[0, 1, 2, 3, 4].map(score => (
          <option key={score} value={score}>
            {score} - {descriptions[score]}
          </option>
        ))}
      </select>
    </div>
  );
};
```

#### B.4 バリデーション仕様

##### B.4.1 フロントエンドバリデーション

```javascript
const validateScores = (scores) => {
  const errors = [];
  
  // 必須チェック
  Object.entries(scores).forEach(([axis, score]) => {
    if (score === null || score === undefined) {
      errors.push(`${axis}の評価が未入力です`);
    }
  });
  
  // 範囲チェック
  Object.entries(scores).forEach(([axis, score]) => {
    if (score !== null && (score < 0 || score > 4)) {
      errors.push(`${axis}の評価は0-4の範囲で入力してください`);
    }
  });
  
  return errors;
};
```

##### B.4.2 バックエンドバリデーション

```python
from pydantic import BaseModel, validator

class AnnotationSubmission(BaseModel):
    task_id: str
    scores: Dict[str, int]
    confidence_flag: str
    timestamp_start: datetime
    timestamp_end: datetime
    
    @validator('scores')
    def validate_scores(cls, v):
        required_axes = {'social', 'avoidant', 'mechanical', 'self'}
        if set(v.keys()) != required_axes:
            raise ValueError(f"全ての軸の評価が必要です: {required_axes}")
        
        for axis, score in v.items():
            if not 0 <= score <= 4:
                raise ValueError(f"{axis}の値は0-4の範囲である必要があります")
        
        return v
    
    @validator('confidence_flag')
    def validate_confidence(cls, v):
        if v not in ['certain', 'uncertain']:
            raise ValueError("confidence_flagは'certain'または'uncertain'である必要があります")
        return v
```

#### B.5 レスポンシブデザイン

```css
/* ブレークポイント定義 */
.annotator-workspace {
  display: grid;
  gap: 20px;
  padding: 20px;
}

/* デスクトップ（1024px以上） */
@media (min-width: 1024px) {
  .annotator-workspace {
    grid-template-columns: 1fr 2fr;
    grid-template-areas:
      "history main"
      "history actions";
  }
  
  .dialogue-history {
    grid-area: history;
    max-height: 600px;
    overflow-y: auto;
  }
}

/* タブレット（768px-1023px） */
@media (min-width: 768px) and (max-width: 1023px) {
  .annotator-workspace {
    grid-template-columns: 1fr;
    grid-template-areas:
      "history"
      "main"
      "actions";
  }
  
  .dialogue-history {
    max-height: 300px;
  }
}
```