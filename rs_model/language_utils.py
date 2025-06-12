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

def detect_language(text: str) -> str:
    """
    Detects the language code of the given text using the langdetect library.

    Args:
        text (str): The input text for language detection.

    Returns:
        str: The detected language code (e.g., 'en', 'vi').
             Returns 'en' (English) by default if the input is empty, None,
             or if language detection fails.
    """
    if not text:  # Handle empty or None input explicitly
        return 'en'
    try:
        return detect(text)
    except LangDetectException:
        # Default to English if detection fails
        return 'en'


def get_language_name(text):
    """Detects the language and returns its full name."""
    lang_code = detect_language(text)
    return LANGUAGE_MAPPING.get(lang_code, VIETNAMESE)


def remove_similar_keywords(keywords: list[str], threshold: int = 80) -> list[str]:
    """Removes similar keywords from a list based on a similarity threshold.

    This function iterates through a list of keywords, normalizes them (lowercase, strip whitespace),
    and adds a keyword to the result list only if it's not too similar to any keyword
    already in the result list. Similarity is determined using partial string matching.

    Args:
        keywords (list[str]): A list of strings, where each string is a keyword.
        threshold (int, optional): The similarity threshold (0-100). If the partial ratio
                                   similarity between two keywords is above this threshold,
                                   they are considered similar. Defaults to 80.
    Returns:
        list[str]: A new list of unique keywords with similar ones removed.
    """
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


def split_string_to_keywords(text: str) -> list[str]:
    """Splits a string into a comma-separated list of keywords.
    Args:
        text: The input string.
    Returns:
        A list of keywords.
    """
    if not text:
        return []  # Return an empty list if the input string is empty

    keywords = [keyword.strip() for keyword in text.split(',')]
    return keywords
