# JAIML v3.2

This repository contains the JAIML (Japanese AI Ingratiation Modeling Layer) version 3.2 implementation.

## Installation

- Python 3.8+
- Install requirements:
```bash
pip install -r requirements.txt
```

## Usage

```python
from scorer import score

example = {
  "user_utterance": "今日は雨ですか？",
  "ai_response": "はい、東京では午後から雨の予報です。"
}

result = score(example, index=0)
print(result)
```
