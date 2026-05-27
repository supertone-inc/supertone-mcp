"""Tests for MCP server entry point and tool registration (ISSUE-007)."""

import pathlib

from supertone_tts_mcp.server import mcp


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


class TestMainFunction:
    def test_main_is_callable(self):
        from supertone_tts_mcp.server import main

        assert callable(main)


class TestMainModule:
    def test_main_module_exists(self):
        main_path = (
            pathlib.Path(__file__).parent.parent
            / "src"
            / "supertone_tts_mcp"
            / "__main__.py"
        )
        assert main_path.exists()

    def test_main_module_imports_main(self):
        source = (
            pathlib.Path(__file__).parent.parent
            / "src"
            / "supertone_tts_mcp"
            / "__main__.py"
        ).read_text()
        assert "from supertone_tts_mcp.server import main" in source
