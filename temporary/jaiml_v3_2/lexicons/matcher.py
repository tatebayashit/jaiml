# src/model/jaiml_v3_2/lexicons/matcher.py
import re
import yaml

class LexiconMatcher:
    def __init__(self, lexicon_path: str):
        # Load lexicons from YAML file
        with open(lexicon_path, 'r', encoding='utf-8') as f:
            self.lexicons = yaml.safe_load(f)

    def match(self, sentence: str):
        """
        Match lexicon categories against the given sentence.
        Returns a dict: {category_name: [matched_strings]}
        """
        results = {}
        for category, terms in self.lexicons.items():
            matches = []
            for term in terms:
                if re.search(re.escape(term), sentence):
                    matches.append(term)
            results[category] = matches
        return results
