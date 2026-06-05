"""Tests for MCP server entry point and tool registration (ISSUE-007)."""

import pathlib

from supertone_mcp.server import mcp


class TestToolRegistration:
    def test_registers_v02_tools(self):
        """ISSUE-016: v0.2 surface now includes get_voice + get_credit_balance.

        Replaces the prior fixed-count assertion (== 2) with a superset check
        so future v0.2 tools (preview_voice, predict_duration, clone_voice,
        etc.) can be added without churning this test.
        """
        tools = mcp._tool_manager._tools
        required = {
            "text_to_speech",
            "search_voice",
            "get_voice",
            "get_credit_balance",
        }
        missing = required - set(tools.keys())
        assert not missing, f"Missing v0.2 tools: {missing}"

    def test_text_to_speech_tool_exists(self):
        tools = mcp._tool_manager._tools
        assert "text_to_speech" in tools

    def test_search_voice_tool_exists(self):
        tools = mcp._tool_manager._tools
        assert "search_voice" in tools

    def test_get_voice_tool_exists(self):
        """ISSUE-016 AC #5: get_voice is registered."""
        tools = mcp._tool_manager._tools
        assert "get_voice" in tools

    def test_get_credit_balance_tool_exists(self):
        """ISSUE-016 AC #5: get_credit_balance is registered."""
        tools = mcp._tool_manager._tools
        assert "get_credit_balance" in tools

    def test_list_voices_tool_removed(self):
        """v0.2 breaking change: list_voices is removed (ISSUE-015)."""
        tools = mcp._tool_manager._tools
        assert "list_voices" not in tools

    def test_text_to_speech_description(self):
        tool = mcp._tool_manager._tools["text_to_speech"]
        desc = tool.description
        assert "speech" in desc
        # text_to_speech description should refer to search_voice (not list_voices)
        assert "search_voice" in desc
        assert "list_voices" not in desc
        assert "23 languages" in desc

    def test_search_voice_description_matches_ux_spec(self):
        """Description must follow docs/ux_spec.md §2.3 wording."""
        tool = mcp._tool_manager._tools["search_voice"]
        desc = tool.description
        # Core wording from the UX spec
        assert "Search the Supertone voice catalog" in desc
        assert "AND semantics" in desc
        # Every filter parameter is enumerated in the description
        for kw in (
            "name",
            "description",
            "language",
            "gender",
            "age",
            "use_case",
            "style",
            "model",
        ):
            assert kw in desc
        # Behavior fallback documented
        assert "Filters applied" in desc

    def test_text_to_speech_has_text_parameter(self):
        tool = mcp._tool_manager._tools["text_to_speech"]
        schema = tool.parameters
        assert "text" in schema["properties"]

    def test_text_to_speech_text_is_required(self):
        tool = mcp._tool_manager._tools["text_to_speech"]
        schema = tool.parameters
        assert "text" in schema.get("required", [])

    def test_text_to_speech_has_model_parameter(self):
        tool = mcp._tool_manager._tools["text_to_speech"]
        schema = tool.parameters
        assert "model" in schema["properties"]

    def test_text_to_speech_has_output_mode_and_autoplay_params(self):
        """ISSUE-022: per-call output_mode + autoplay replace env vars."""
        tool = mcp._tool_manager._tools["text_to_speech"]
        properties = tool.parameters["properties"]
        assert "output_mode" in properties
        assert "autoplay" in properties

    def test_text_to_speech_output_mode_and_autoplay_optional(self):
        """ISSUE-022: both new params are optional (have defaults)."""
        tool = mcp._tool_manager._tools["text_to_speech"]
        required = tool.parameters.get("required", [])
        assert "output_mode" not in required
        assert "autoplay" not in required

    def test_text_to_speech_description_documents_param_migration(self):
        """ISSUE-022: docstring/description documents the env-var replacement
        and that autoplay defaults to false."""
        tool = mcp._tool_manager._tools["text_to_speech"]
        desc = tool.description
        assert "output_mode" in desc
        assert "autoplay" in desc

    def test_text_to_speech_has_streaming_param(self):
        """ISSUE-023: streaming boolean param present, optional, default false."""
        tool = mcp._tool_manager._tools["text_to_speech"]
        schema = tool.parameters
        properties = schema["properties"]
        assert "streaming" in properties
        # Boolean type
        assert properties["streaming"].get("type") == "boolean"
        # Default false
        assert properties["streaming"].get("default") is False
        # Optional (not in required)
        assert "streaming" not in schema.get("required", [])

    def test_text_to_speech_streaming_documents_sona1_requirement(self):
        """ISSUE-023: streaming description/docstring states sona_speech_1-only."""
        tool = mcp._tool_manager._tools["text_to_speech"]
        # The per-parameter description lives in the JSON schema; the
        # sona_speech_1 requirement must be discoverable to the LLM.
        prop_desc = tool.parameters["properties"]["streaming"].get("description", "")
        haystack = (prop_desc + " " + (tool.description or "")).lower()
        assert "sona_speech_1" in haystack

    def test_search_voice_all_filters_optional(self):
        """search_voice must accept zero filters."""
        tool = mcp._tool_manager._tools["search_voice"]
        schema = tool.parameters
        required = schema.get("required", [])
        for kw in (
            "language",
            "gender",
            "age",
            "use_case",
            "style",
            "model",
            "name",
            "description",
        ):
            assert kw not in required, f"{kw} should be optional"

    def test_search_voice_exposes_all_filter_params(self):
        """All eight filter params must be present in the JSON Schema."""
        tool = mcp._tool_manager._tools["search_voice"]
        schema = tool.parameters
        properties = schema["properties"]
        for kw in (
            "language",
            "gender",
            "age",
            "use_case",
            "style",
            "model",
            "name",
            "description",
        ):
            assert kw in properties, f"{kw} missing from search_voice schema"

    # --- ISSUE-016: get_voice / get_credit_balance schema + description ---

    def test_get_voice_description_matches_ux_spec(self):
        """Description must reflect docs/ux_spec.md §2.4."""
        tool = mcp._tool_manager._tools["get_voice"]
        desc = tool.description
        assert "Fetch full detail" in desc
        assert "voice_id" in desc
        # Mentions the canonical output fields
        for kw in (
            "name",
            "description",
            "age",
            "gender",
            "use_cases",
            "languages",
            "styles",
            "models",
            "sample count",
            "thumbnail",
        ):
            assert kw in desc, f"missing keyword '{kw}' from get_voice description"
        # Cross-references the sister tool
        assert "preview_voice" in desc

    def test_get_voice_has_voice_id_parameter(self):
        tool = mcp._tool_manager._tools["get_voice"]
        schema = tool.parameters
        assert "voice_id" in schema["properties"]

    def test_get_voice_voice_id_is_required(self):
        """voice_id is the only param and it is REQUIRED."""
        tool = mcp._tool_manager._tools["get_voice"]
        schema = tool.parameters
        assert "voice_id" in schema.get("required", [])

    def test_get_credit_balance_description_matches_ux_spec(self):
        """Description must reflect docs/ux_spec.md §2.5."""
        tool = mcp._tool_manager._tools["get_credit_balance"]
        desc = tool.description
        assert "credit balance" in desc.lower()
        assert "API key" in desc

    def test_get_credit_balance_has_no_required_params(self):
        """get_credit_balance takes no parameters."""
        tool = mcp._tool_manager._tools["get_credit_balance"]
        schema = tool.parameters
        # Either no required list or empty
        assert not schema.get("required")
        # properties should be empty (or absent)
        props = schema.get("properties", {})
        assert props == {} or props is None

    # --- ISSUE-017: preview_voice schema + description ---

    def test_preview_voice_tool_exists(self):
        """ISSUE-017 AC: preview_voice is registered."""
        tools = mcp._tool_manager._tools
        assert "preview_voice" in tools

    def test_preview_voice_description_matches_ux_spec(self):
        """Description must reflect docs/ux_spec.md §2.6."""
        tool = mcp._tool_manager._tools["preview_voice"]
        desc = tool.description
        # Core wording from the UX spec
        assert "sample audio URLs" in desc
        assert "voice" in desc.lower()
        # Documents the optional filters
        for kw in ("language", "style", "model"):
            assert kw in desc, f"missing keyword '{kw}' from preview_voice description"
        # Documents the no-autoplay constraint
        assert "NOT play" in desc or "not play" in desc

    def test_preview_voice_has_voice_id_parameter(self):
        tool = mcp._tool_manager._tools["preview_voice"]
        schema = tool.parameters
        assert "voice_id" in schema["properties"]

    def test_preview_voice_voice_id_is_required(self):
        """voice_id is the only REQUIRED param."""
        tool = mcp._tool_manager._tools["preview_voice"]
        schema = tool.parameters
        assert "voice_id" in schema.get("required", [])

    def test_preview_voice_filter_params_are_optional(self):
        """language/style/model are all optional filters."""
        tool = mcp._tool_manager._tools["preview_voice"]
        schema = tool.parameters
        required = schema.get("required", [])
        for kw in ("language", "style", "model"):
            assert kw not in required, f"{kw} should be optional"

    def test_preview_voice_exposes_all_filter_params(self):
        """All three filter params must be present in the JSON Schema."""
        tool = mcp._tool_manager._tools["preview_voice"]
        schema = tool.parameters
        properties = schema["properties"]
        for kw in ("language", "style", "model"):
            assert kw in properties, f"{kw} missing from preview_voice schema"

    # --- ISSUE-018: predict_duration schema + description ---

    def test_predict_duration_tool_exists(self):
        """ISSUE-018 AC #6: predict_duration is registered."""
        tools = mcp._tool_manager._tools
        assert "predict_duration" in tools

    def test_predict_duration_description_matches_ux_spec(self):
        """Description must reflect docs/ux_spec.md §2.7."""
        tool = mcp._tool_manager._tools["predict_duration"]
        desc = tool.description
        # Core wording from the UX spec — does not synthesize audio
        assert "duration" in desc.lower()
        assert "300" in desc
        # Mentions text_to_speech parameter parity
        assert "text_to_speech" in desc
        # Mentions the credit/cost rationale
        assert "credit" in desc.lower() or "cost" in desc.lower()

    def test_predict_duration_has_text_parameter(self):
        tool = mcp._tool_manager._tools["predict_duration"]
        schema = tool.parameters
        assert "text" in schema["properties"]

    def test_predict_duration_text_is_required(self):
        """text is the only REQUIRED parameter (mirrors text_to_speech)."""
        tool = mcp._tool_manager._tools["predict_duration"]
        schema = tool.parameters
        assert "text" in schema.get("required", [])

    def test_predict_duration_optional_params_match_text_to_speech(self):
        """predict_duration mirrors the SYNTHESIS-INPUT params of text_to_speech.

        text_to_speech exposes (voice_id, language, output_format, model,
        speed, pitch_shift, style) as optional synthesis inputs, plus the
        output/routing-handling params (output_mode, autoplay added in
        ISSUE-022; streaming added in ISSUE-023). predict_duration produces no
        audio, so it intentionally excludes the output/routing params but must
        match on every synthesis input.
        """
        tts_tool = mcp._tool_manager._tools["text_to_speech"]
        pd_tool = mcp._tool_manager._tools["predict_duration"]
        tts_props = set(tts_tool.parameters["properties"].keys())
        pd_props = set(pd_tool.parameters["properties"].keys())
        # output/routing handling is synthesis-only; predict_duration omits it.
        output_handling = {"output_mode", "autoplay", "streaming"}
        synthesis_inputs = tts_props - output_handling
        assert synthesis_inputs == pd_props, (
            f"predict_duration schema mismatch with text_to_speech: "
            f"missing={synthesis_inputs - pd_props}, "
            f"extra={pd_props - synthesis_inputs}"
        )
        # The output/routing-handling params must NOT appear on predict_duration.
        assert output_handling.isdisjoint(pd_props)

    def test_predict_duration_optional_params_are_optional(self):
        """All non-text params are optional."""
        tool = mcp._tool_manager._tools["predict_duration"]
        schema = tool.parameters
        required = schema.get("required", [])
        for kw in (
            "voice_id",
            "language",
            "output_format",
            "model",
            "speed",
            "pitch_shift",
            "style",
        ):
            assert kw not in required, f"{kw} should be optional"

    # --- ISSUE-019: clone_voice schema + description ---

    def test_clone_voice_tool_exists(self):
        """ISSUE-019 AC #7: clone_voice is registered."""
        tools = mcp._tool_manager._tools
        assert "clone_voice" in tools

    def test_clone_voice_description_matches_ux_spec(self):
        """Description must reflect docs/ux_spec.md §2.8."""
        tool = mcp._tool_manager._tools["clone_voice"]
        desc = tool.description
        # Core wording from the UX spec
        assert "custom voice" in desc.lower()
        assert "WAV" in desc
        assert "MP3" in desc
        # Size constraint must be documented
        assert "3MB" in desc or "3 MB" in desc
        # Single-file constraint must be documented
        assert "one" in desc.lower() or "single" in desc.lower()
        # Mentions how the new voice can be used
        assert "text_to_speech" in desc

    def test_clone_voice_has_name_parameter(self):
        tool = mcp._tool_manager._tools["clone_voice"]
        schema = tool.parameters
        assert "name" in schema["properties"]

    def test_clone_voice_has_audio_path_parameter(self):
        tool = mcp._tool_manager._tools["clone_voice"]
        schema = tool.parameters
        assert "audio_path" in schema["properties"]

    def test_clone_voice_has_description_parameter(self):
        tool = mcp._tool_manager._tools["clone_voice"]
        schema = tool.parameters
        assert "description" in schema["properties"]

    def test_clone_voice_name_is_required(self):
        """AC #7: name is required."""
        tool = mcp._tool_manager._tools["clone_voice"]
        schema = tool.parameters
        assert "name" in schema.get("required", [])

    def test_clone_voice_audio_path_is_required(self):
        """AC #7: audio_path is required."""
        tool = mcp._tool_manager._tools["clone_voice"]
        schema = tool.parameters
        assert "audio_path" in schema.get("required", [])

    def test_clone_voice_description_is_optional(self):
        """AC #7: description is optional."""
        tool = mcp._tool_manager._tools["clone_voice"]
        schema = tool.parameters
        required = schema.get("required", [])
        assert "description" not in required

    # --- ISSUE-020: search_custom_voice / edit_custom_voice / delete_custom_voice ---

    def test_search_custom_voice_tool_exists(self):
        """ISSUE-020 AC #8: search_custom_voice is registered."""
        tools = mcp._tool_manager._tools
        assert "search_custom_voice" in tools

    def test_edit_custom_voice_tool_exists(self):
        """ISSUE-020 AC #8: edit_custom_voice is registered."""
        tools = mcp._tool_manager._tools
        assert "edit_custom_voice" in tools

    def test_delete_custom_voice_tool_exists(self):
        """ISSUE-020 AC #8: delete_custom_voice is registered."""
        tools = mcp._tool_manager._tools
        assert "delete_custom_voice" in tools

    def test_search_custom_voice_description_matches_ux_spec(self):
        """Description must reflect docs/ux_spec.md §2.9."""
        tool = mcp._tool_manager._tools["search_custom_voice"]
        desc = tool.description
        assert "custom" in desc.lower()
        assert "name" in desc and "description" in desc
        # Documents partial-match filtering
        assert "partial" in desc.lower()

    def test_search_custom_voice_filters_optional(self):
        tool = mcp._tool_manager._tools["search_custom_voice"]
        schema = tool.parameters
        required = schema.get("required", [])
        assert "name" not in required
        assert "description" not in required

    def test_search_custom_voice_exposes_filter_params(self):
        tool = mcp._tool_manager._tools["search_custom_voice"]
        schema = tool.parameters
        properties = schema["properties"]
        assert "name" in properties
        assert "description" in properties

    def test_edit_custom_voice_description_matches_ux_spec(self):
        """Description must reflect docs/ux_spec.md §2.10."""
        tool = mcp._tool_manager._tools["edit_custom_voice"]
        desc = tool.description
        assert "name" in desc and "description" in desc
        # At-least-one rule must be documented in the tool description.
        assert "at least one" in desc.lower()

    def test_edit_custom_voice_voice_id_is_required(self):
        tool = mcp._tool_manager._tools["edit_custom_voice"]
        schema = tool.parameters
        assert "voice_id" in schema.get("required", [])

    def test_edit_custom_voice_name_and_description_optional(self):
        tool = mcp._tool_manager._tools["edit_custom_voice"]
        schema = tool.parameters
        required = schema.get("required", [])
        assert "name" not in required
        assert "description" not in required

    def test_edit_custom_voice_exposes_all_params(self):
        tool = mcp._tool_manager._tools["edit_custom_voice"]
        schema = tool.parameters
        properties = schema["properties"]
        for kw in ("voice_id", "name", "description"):
            assert kw in properties

    def test_delete_custom_voice_description_warns_irreversible(self):
        """Description must call out the irreversibility per UX spec §2.11."""
        tool = mcp._tool_manager._tools["delete_custom_voice"]
        desc = tool.description
        assert "IRREVERSIBLE" in desc
        # Encourages user confirmation since v0.2 has no in-tool gate.
        assert "confirm" in desc.lower()

    def test_delete_custom_voice_voice_id_is_required(self):
        tool = mcp._tool_manager._tools["delete_custom_voice"]
        schema = tool.parameters
        assert "voice_id" in schema.get("required", [])

    def test_delete_custom_voice_has_voice_id_parameter(self):
        tool = mcp._tool_manager._tools["delete_custom_voice"]
        schema = tool.parameters
        assert "voice_id" in schema["properties"]


class TestMainFunction:
    def test_main_is_callable(self):
        from supertone_mcp.server import main

        assert callable(main)


class TestMainModule:
    def test_main_module_exists(self):
        main_path = (
            pathlib.Path(__file__).parent.parent
            / "src"
            / "supertone_mcp"
            / "__main__.py"
        )
        assert main_path.exists()

    def test_main_module_imports_main(self):
        source = (
            pathlib.Path(__file__).parent.parent
            / "src"
            / "supertone_mcp"
            / "__main__.py"
        ).read_text()
        assert "from supertone_mcp.server import main" in source
