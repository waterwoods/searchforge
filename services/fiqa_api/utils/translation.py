"""
Translation Utilities
====================
Lightweight translation support for Chinese-English queries.

Uses argos-translate as default (offline, no API keys needed).
Falls back gracefully if translation is unavailable.
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Environment variables (read at runtime, not module load time)
# Use functions to read env vars at call time, not module import time
def _get_translation_enabled():
    """Get TRANSLATION_ENABLED from environment (read at call time, not module load)"""
    return os.getenv("TRANSLATION_ENABLED", "0") == "1"

def _get_translation_provider():
    """Get TRANSLATION_PROVIDER from environment (read at call time, not module load)"""
    return os.getenv("TRANSLATION_PROVIDER", "argos").lower()

def _get_translate_sources_to_zh():
    """Get TRANSLATE_SOURCES_TO_ZH from environment (read at call time, not module load)"""
    return os.getenv("TRANSLATE_SOURCES_TO_ZH", "1") == "1"

# Module-level constants for backward compatibility (but they're functions now)
# These will be called at runtime, not module load time
TRANSLATION_ENABLED = None  # Will be read via _get_translation_enabled()
TRANSLATION_PROVIDER = None  # Will be read via _get_translation_provider()
TRANSLATE_SOURCES_TO_ZH = None  # Will be read via _get_translate_sources_to_zh()

# Translation provider instances (lazy loaded)
_translator_zh_to_en = None
_translator_en_to_zh = None
_translation_available = False


def _init_translator():
    """Initialize translation provider (lazy loading)."""
    global _translator_zh_to_en, _translator_en_to_zh, _translation_available
    
    if not _get_translation_enabled():
        logger.info("Translation disabled (TRANSLATION_ENABLED=0)")
        return
    
    if _get_translation_provider() == "none":
        logger.info("Translation provider set to 'none'")
        return
    
    if _get_translation_provider() == "argos":
        try:
            from argostranslate import translate
            
            # Get installed languages
            installed_languages = translate.get_installed_languages()
            zh_lang = None
            en_lang = None
            for lang in installed_languages:
                if lang.code == "zh":
                    zh_lang = lang
                elif lang.code == "en":
                    en_lang = lang
            
            if not zh_lang or not en_lang:
                logger.warning("Argos Translate: Chinese or English language package not installed. Run: python -m argostranslate.argostranslate --install-packages zh en")
                return
            
            # Get translation pairs using get_translation_from_codes (correct API)
            zh_to_en_pair = None
            en_to_zh_pair = None
            try:
                zh_to_en_pair = translate.get_translation_from_codes("zh", "en")
                en_to_zh_pair = translate.get_translation_from_codes("en", "zh")
            except Exception as e:
                logger.warning(f"Failed to get translation pairs: {e}")
                return
            
            if not zh_to_en_pair or not en_to_zh_pair:
                logger.warning("Argos Translate: Translation pairs not installed. Run: python -m argostranslate.argostranslate --install-packages zh en")
                return
            
            # Store the LanguagePair objects
            _translator_zh_to_en = zh_to_en_pair
            _translator_en_to_zh = en_to_zh_pair
            _translation_available = True
            logger.info("✅ Argos Translate initialized (zh↔en)")
            
        except ImportError:
            logger.warning(
                "argostranslate not installed. Install with: pip install argostranslate"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Argos Translate: {e}")
            import traceback
            logger.debug(traceback.format_exc())
    
    else:
        logger.warning(f"Unknown translation provider: {_get_translation_provider()}")


def detect_lang(text: str) -> str:
    """
    Detect language of text.
    
    Returns: "zh", "en", or "unknown"
    """
    if not text:
        return "unknown"
    
    # Simple heuristic: check for Chinese characters
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in text)
    if has_chinese:
        return "zh"
    
    # Check for Spanish characters (optional, for future use)
    has_spanish = any(c in "áéíóúñü¿¡" for c in text.lower())
    if has_spanish:
        return "es"
    
    # Default to English
    return "en"


def translate_zh_to_en(text: str) -> Optional[str]:
    """
    Translate Chinese text to English.
    
    Returns translated text, or None if translation unavailable.
    """
    global _translator_zh_to_en, _translation_available
    
    if not _get_translation_enabled():
        return None
    
    if not text or not text.strip():
        return text
    
    # Lazy initialization
    if _translator_zh_to_en is None and _translation_available is False:
        _init_translator()
    
    if not _translation_available or _translator_zh_to_en is None:
        logger.debug("Translation unavailable, returning None")
        return None
    
    try:
        import argostranslate.translate
        # Use language codes directly
        if isinstance(_translator_zh_to_en, tuple):
            from_code, to_code = _translator_zh_to_en
            result = argostranslate.translate.translate(text, from_code, to_code)
        else:
            result = argostranslate.translate.translate(text, "zh", "en")
        logger.debug(f"Translated: {text[:50]}... -> {result[:50]}...")
        return result
    except Exception as e:
        logger.error(f"Translation error (zh->en): {e}")
        return None


def self_test() -> Dict[str, Any]:
    """
    Self-test function to verify translation is working.
    
    Returns:
        Dict with test results and status
    """
    result = {
        "translation_enabled": _get_translation_enabled(),
        "provider": _get_translation_provider(),
        "available": False,
        "test_passed": False,
        "test_input": "加州最低汽车保险要求是什么？",
        "test_output": None,
        "error": None
    }
    
    if not _get_translation_enabled():
        result["error"] = "Translation not enabled (TRANSLATION_ENABLED != 1)"
        return result
    
    if _get_translation_provider() != "argos":
        result["error"] = f"Translation provider is '{_get_translation_provider()}', expected 'argos'"
        return result
    
    try:
        _init_translator()
        result["available"] = is_translation_available()
        
        if result["available"]:
            translated = translate_zh_to_en(result["test_input"])
            if translated:
                result["test_output"] = translated
                result["test_passed"] = True
            else:
                result["error"] = "Translation returned None"
        else:
            result["error"] = "Translation service not available after initialization"
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Translation self-test failed: {e}", exc_info=True)
    
    return result


def translate_en_to_zh(text: str) -> Optional[str]:
    """
    Translate English text to Chinese.
    
    Returns translated text, or None if translation unavailable.
    """
    global _translator_en_to_zh, _translation_available
    
    if not _get_translation_enabled():
        return None
    
    if not _get_translate_sources_to_zh():
        return None
    
    if not text or not text.strip():
        return text
    
    # Lazy initialization
    if _translator_en_to_zh is None and _translation_available is False:
        _init_translator()
    
    if not _translation_available or _translator_en_to_zh is None:
        logger.debug("Translation unavailable, returning None")
        return None
    
    try:
        import argostranslate.translate
        # Use language codes directly
        if isinstance(_translator_en_to_zh, tuple):
            from_code, to_code = _translator_en_to_zh
            result = argostranslate.translate.translate(text, from_code, to_code)
        else:
            result = argostranslate.translate.translate(text, "en", "zh")
        logger.debug(f"Translated: {text[:50]}... -> {result[:50]}...")
        return result
    except Exception as e:
        logger.error(f"Translation error (en->zh): {e}")
        return None


def translation_debug_state() -> Dict[str, Any]:
    """
    Return debug state for translation system.
    Used for diagnostics and debugging.
    """
    state = {
        "enabled_env": os.getenv("TRANSLATION_ENABLED", "NOT_SET"),
        "provider": os.getenv("TRANSLATION_PROVIDER", "NOT_SET"),
        "argos_import_ok": False,
        "argos_languages_count": 0,
        "argos_has_zh_en": False,
        "error": None
    }
    
    try:
        import argostranslate.package
        import argostranslate.translate
        state["argos_import_ok"] = True
        
        # Get installed languages
        installed_languages = argostranslate.translate.get_installed_languages()
        state["argos_languages_count"] = len(installed_languages)
        
        # Check for zh and en
        lang_codes = [lang.code for lang in installed_languages]
        state["argos_has_zh_en"] = "zh" in lang_codes and "en" in lang_codes
        
        # Test translation if available
        if state["argos_has_zh_en"]:
            try:
                test_result = argostranslate.translate.translate("test", "en", "zh")
                if not test_result:
                    state["error"] = "Translation test returned empty"
            except Exception as test_e:
                state["error"] = f"Translation test failed: {str(test_e)}"
                
    except ImportError as e:
        state["error"] = f"argostranslate not installed: {str(e)}"
    except Exception as e:
        state["error"] = f"Error checking translation state: {str(e)}"
    
    return state


def is_translation_available() -> bool:
    """Check if translation is available (runtime check, no caching)."""
    # Use runtime function to check env var, not module-level constant
    if not _get_translation_enabled():
        return False
    
    if _get_translation_provider() != "argos":
        return False
    
    # Check Argos availability at runtime
    try:
        import argostranslate.translate
        installed_languages = argostranslate.translate.get_installed_languages()
        lang_codes = [lang.code for lang in installed_languages]
        if "zh" not in lang_codes or "en" not in lang_codes:
            return False
        
        # Test translation
        test_result = argostranslate.translate.translate("test", "en", "zh")
        return bool(test_result)
    except Exception:
        return False
