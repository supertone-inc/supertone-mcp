"""Guard tests: SUPPORTED_* constants must stay in sync with the installed SDK enums.

These exist because the lists drifted from the SDK twice (models in ISSUE-021,
languages in ISSUE-028). When the `supertone` SDK adds models/languages/formats,
these tests fail loudly at CI time instead of silently rejecting valid inputs in
`validate_model` / `validate_language` / `validate_output_format`.
"""

from supertone import models

from supertone_mcp.constants import (
    SUPPORTED_FORMATS,
    SUPPORTED_LANGUAGES,
    SUPPORTED_MODELS,
)


def _enum_values(enum_cls) -> set[str]:
    return {member.value for member in enum_cls}


def test_supported_models_match_sdk_enum() -> None:
    sdk = _enum_values(models.APIConvertTextToSpeechUsingCharacterRequestModel)
    assert set(SUPPORTED_MODELS) == sdk, (
        f"SUPPORTED_MODELS out of sync with SDK. "
        f"Missing: {sorted(sdk - set(SUPPORTED_MODELS))}, "
        f"Extra: {sorted(set(SUPPORTED_MODELS) - sdk)}"
    )
    # no duplicates in the constant
    assert len(SUPPORTED_MODELS) == len(set(SUPPORTED_MODELS))


def test_supported_languages_match_sdk_enum() -> None:
    sdk = _enum_values(models.APIConvertTextToSpeechUsingCharacterRequestLanguage)
    assert set(SUPPORTED_LANGUAGES) == sdk, (
        f"SUPPORTED_LANGUAGES out of sync with SDK. "
        f"Missing: {sorted(sdk - set(SUPPORTED_LANGUAGES))}, "
        f"Extra: {sorted(set(SUPPORTED_LANGUAGES) - sdk)}"
    )
    assert len(SUPPORTED_LANGUAGES) == len(set(SUPPORTED_LANGUAGES))


def test_supported_formats_match_sdk_enum() -> None:
    sdk = _enum_values(models.APIConvertTextToSpeechUsingCharacterRequestOutputFormat)
    assert set(SUPPORTED_FORMATS) == sdk


def test_predict_duration_enums_match_tts_enums() -> None:
    """predict_duration's model/language enums must not diverge from TTS's."""
    tts_models = _enum_values(models.APIConvertTextToSpeechUsingCharacterRequestModel)
    predict_models = _enum_values(models.PredictTTSDurationRequestModel)
    assert tts_models == predict_models

    tts_langs = _enum_values(models.APIConvertTextToSpeechUsingCharacterRequestLanguage)
    predict_langs = _enum_values(models.PredictTTSDurationRequestLanguage)
    assert tts_langs == predict_langs
