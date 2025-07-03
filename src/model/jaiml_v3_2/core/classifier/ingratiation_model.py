# src/model/jaiml_v3_2/core/classifier/ingratiation_model.py
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel

class MLPHead(nn.Module):
    def __init__(self, input_dim: int):
        super().__init__()
        self.linear1 = nn.Linear(input_dim, 128)
        self.dropout = nn.Dropout(0.3)
        self.linear2 = nn.Linear(128, 1)

    def forward(self, x):
        x = torch.relu(self.linear1(x))
        x = self.dropout(x)
        x = torch.sigmoid(self.linear2(x))
        return x

class IngratiationModel:
    def __init__(self, transformer_model_name: str):
        # Load pre-trained Japanese BERT (or similar) model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(transformer_model_name)
        self.encoder = AutoModel.from_pretrained(transformer_model_name)
        # MLP heads for 4 categories; input is [CLS] embedding dim + 3 feature dims
        emb_dim = self.encoder.config.hidden_size
        self.social_head = MLPHead(emb_dim + 3)
        self.avoidant_head = MLPHead(emb_dim + 3)
        self.mechanical_head = MLPHead(emb_dim + 3)
        self.self_head = MLPHead(emb_dim + 3)

    def forward(self, user_text: str, response_text: str, features: dict):
        # Encode texts with transformer
        inputs = self.tokenizer(user_text, response_text, return_tensors='pt', padding=True, truncation=True)
        outputs = self.encoder(**inputs)
        # Use [CLS] token representation (assume last_hidden_state[:,0,:])
        cls_emb = outputs.last_hidden_state[:, 0, :]
        # Retrieve features (each a scalar)
        sem = torch.tensor([features['semantic_congruence']])
        sent = torch.tensor([features['sentiment_emphasis_score']])
        user_rep = torch.tensor([features['user_repetition_ratio']])
        modal = torch.tensor([features['modal_expression_ratio']])
        resp_dep = torch.tensor([features['response_dependency']])
        assert_score = torch.tensor([features['assertiveness_score']])
        lex_div = torch.tensor([features['lexical_diversity_inverse']])
        templ = torch.tensor([features['template_match_rate']])
        novelty = torch.tensor([features['tfidf_novelty']])
        self_ref = torch.tensor([features['self_ref_pos_score']])
        ai_subj = torch.tensor([features['ai_subject_ratio']])
        self_prom = torch.tensor([features['self_promotion_intensity'] * 0.5])
        # Concatenate embedding with features per category
        social_input = torch.cat([cls_emb, torch.stack([sem, sent, user_rep], dim=1)], dim=1)
        avoidant_input = torch.cat([cls_emb, torch.stack([modal, resp_dep, assert_score], dim=1)], dim=1)
        mechanical_input = torch.cat([cls_emb, torch.stack([lex_div, templ, 1.0 - novelty], dim=1)], dim=1)
        self_input = torch.cat([cls_emb, torch.stack([self_ref, ai_subj, self_prom], dim=1)], dim=1)
        # Compute scores via sigmoid MLP heads
        social_score = self.social_head(social_input)
        avoidant_score = self.avoidant_head(avoidant_input)
        mechanical_score = self.mechanical_head(mechanical_input)
        self_score = self.self_head(self_input)
        return {
            'social': social_score.item(),
            'avoidant': avoidant_score.item(),
            'mechanical': mechanical_score.item(),
            'self': self_score.item()
        }

def compute_main_category(scores: dict) -> str:
    """
    Determine main category: highest score with tie-breaking priority:
    self > social > avoidant > mechanical
    """
    primary = max(scores, key=scores.get)
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_scores) > 1:
        top, second = sorted_scores[0][1], sorted_scores[1][1]
        if abs(top - second) < 0.1:
            priorities = ['self', 'social', 'avoidant', 'mechanical']
            for cat in priorities:
                if scores.get(cat) == top:
                    primary = cat
                    break
    return primary
