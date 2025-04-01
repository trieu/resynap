from langdetect import detect, LangDetectException
from rapidfuzz import fuzz  # Faster alternative to fuzzywuzzy

# need Google translate to convert input into English
from google.cloud import translate_v2 as translate
import pprint

VIETNAMESE = "Vietnamese"
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
    return LANGUAGE_MAPPING.get(lang_code, VIETNAMESE)


def remove_similar_keywords(keywords: list[str], threshold: int = 80) -> list[str]:
    unique_keywords = []
    
    for keyword in keywords:
        keyword_lower = keyword.lower().strip()  # Normalize case and strip spaces
        if not any(fuzz.partial_ratio(keyword_lower, existing) > threshold for existing in unique_keywords):
            unique_keywords.append(keyword_lower)
    
    return unique_keywords



def detect_language_using_google(text: str) -> str:
    """detect language
    Args:
        text (str)
    Returns:
        language_code (language_code with default is "en")
    """
    if text == "" or text is None:
        return "en"
    if isinstance(text, bytes):
        text = text.decode("utf-8")
    result = translate.Client().detect_language(text)
    print(result)
    if result['confidence'] > 0.9 :
        return result['language']
    else : 
        return "en"
    
    
# Translates text into the target language.
def translate_text_using_google(text: str, target: str) -> dict:
    """Translates the given text into the target language."""
    if text == "" or text is None:
        return ""
    if isinstance(text, bytes):
        text = text.decode("utf-8")
    result = translate.Client().translate(text, target_language=target)
    return result['translatedText']


def format_string_for_md_slides(rs: str):
    rs = rs.replace('<br/>','\n')
    rs = rs.replace('##','## ')
    return rs

