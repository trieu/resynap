from langdetect import detect, LangDetectException
from thefuzz import fuzz
from thefuzz import process

LANGUAGE_MAPPING = {
    "en": "English",
    "vi": "Vietnamese",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)",
    "ja": "Japanese",
    "ko": "Korean",
    "ru": "Russian"
}

def detect_language(text):
    """Detects the language code of the given text."""
    try:
        return detect(text)
    except LangDetectException:
        return 'en'

def get_language_name(text):
    """Detects the language and returns its full name."""
    lang_code = detect_language(text)
    return LANGUAGE_MAPPING.get(lang_code, "English")

def remove_similar_keywords(keywords, threshold=80):
    unique = []
    for keyword in keywords:
        if not any(fuzz.ratio(keyword, existing) > threshold for existing in unique):
            unique.append(keyword)
    return unique


