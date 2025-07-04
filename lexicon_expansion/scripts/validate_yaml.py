from pydantic import BaseModel, Field, validator
from typing import List, Optional
import yaml

class CandidateItem(BaseModel):
    phrase: str
    frequency: int = Field(ge=1)
    accept: Optional[bool] = None
    note: Optional[str] = None
    
    @validator('phrase')
    def phrase_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('phrase cannot be empty')
        return v.strip()

class CandidateFile(BaseModel):
    metadata: dict
    candidates: List[CandidateItem]
    
    @validator('candidates')
    def check_duplicates(cls, v):
        phrases = [item.phrase for item in v]
        if len(phrases) != len(set(phrases)):
            raise ValueError('Duplicate phrases found')
        return v

def validate_candidate_file(file_path: str) -> bool:
    """候補ファイルの検証"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    try:
        CandidateFile(**data)
        return True
    except Exception as e:
        print(f"Validation error in {file_path}: {e}")
        return False