import os
import pytest


def test_gemini_model_default():
    """gemini_model should default to google/gemini-2.5-flash."""
    from app.config import get_settings
    get_settings.cache_clear()

    os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
    os.environ.setdefault("SUPABASE_ANON_KEY", "test")
    os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test")

    settings = get_settings()
    assert settings.gemini_model == "google/gemini-2.5-flash"
    get_settings.cache_clear()


def test_old_classifier_fields_removed():
    """classifier_mode, classifier_model, classifier_provider should not exist."""
    from app.config import get_settings
    get_settings.cache_clear()

    os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
    os.environ.setdefault("SUPABASE_ANON_KEY", "test")
    os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test")

    settings = get_settings()
    assert not hasattr(settings, "classifier_mode")
    assert not hasattr(settings, "classifier_model")
    assert not hasattr(settings, "classifier_provider")
    get_settings.cache_clear()
