
def text_normalizer(text):
    import unidecode
    import re
    if not text:
        return text
    text = text.upper().strip()
    text = unidecode.unidecode(text)
    return re.sub(r'[^a-zA-Z\s]', '', text)

