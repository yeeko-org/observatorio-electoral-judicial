from typing import Dict, Optional, Tuple


def text_normalizer(text, to_headers=False) -> str:
    import re
    import unidecode
    if not text:
        return text
    final_text = text.upper().strip()
    final_text = unidecode.unidecode(final_text)
    final_text = final_text.replace('Ü', 'U')
    final_text = re.sub(r'[^a-zA-Z0-9\s]', '', final_text)
    final_text = re.sub(r' +', ' ', final_text)
    final_text = re.sub(
        r'(^A-Z)(SA DE CV|SAPI DE CV|SA DE RL|SAB DE CV|S DE RL|S DE RL DE CV)', '', final_text)
    final_text = re.sub(r' +', ' ', final_text)
    final_text = re.sub(r'[^A-Z0-9]', '', final_text)
    final_text = final_text.strip()
    return final_text
