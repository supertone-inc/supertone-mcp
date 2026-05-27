# Registry & Directory Submissions

Copy-paste kit for listing **supertone-mcp** across MCP directories.
The canonical source is the official MCP Registry (already published); most
fields below are reused verbatim across the other directories' submission forms.

> Status of the official registry: **active** —
> `io.github.supertone-inc/supertone-mcp` (see `server.json`).

---

## Canonical metadata (reuse everywhere)

| Field | Value |
|---|---|
| Registry name | `io.github.supertone-inc/supertone-mcp` |
| Display name / title | Supertone TTS |
| PyPI package | `supertone-mcp` |
| Latest version | `0.1.1` |
| Repository | https://github.com/supertone-inc/supertone-mcp |
| Homepage | https://supertone.ai |
| Transport | `stdio` |
| Language / runtime | Python (≥3.12) |
| Scope | Local service (runs on the user's machine) |
| License | MIT |
| Tool count | 10 |
| Categories / tags | text-to-speech, tts, audio, voice, speech-synthesis, voice-cloning, korean |

**Short description (≤100 chars, registry-validated):**

```
High-quality Supertone TTS: voice search, preview, duration prediction, and voice cloning
```

**Longer description:**

```
MCP server for the Supertone TTS API. Generate natural speech, browse and preview the
voice catalog, predict synthesis cost, and create cloned voices — directly from Claude
Desktop, Cursor, or any MCP-compatible client. Supports Korean, English, Japanese, and
20+ other languages, with speed, pitch, and emotion-style control.
```

**Tools (10):**
`text_to_speech`, `predict_duration`, `search_voice`, `get_voice`, `preview_voice`,
`get_credit_balance`, `clone_voice`, `search_custom_voice`, `edit_custom_voice`,
`delete_custom_voice`

**Environment variables:**

| Variable | Required | Notes |
|---|---|---|
| `SUPERTONE_API_KEY` | Yes | Supertone API key |
| `SUPERTONE_MCP_VOICE_ID` | No | Default voice_id |
| `SUPERTONE_OUTPUT_DIR` | No | Audio output dir (default `~/supertone-tts-output/`) |
| `SUPERTONE_MCP_OUTPUT_MODE` | No | `files` / `resources` / `both` |
| `SUPERTONE_MCP_AUTOPLAY` | No | Auto-play on macOS (default `true`) |

---

## Install snippets

```bash
# uvx (recommended)
uvx supertone-mcp

# pip
pip install supertone-mcp
```

```jsonc
// Claude Desktop / Cursor — claude_desktop_config.json
{
  "mcpServers": {
    "supertone-tts": {
      "command": "uvx",
      "args": ["supertone-mcp"],
      "env": { "SUPERTONE_API_KEY": "your-api-key-here" }
    }
  }
}
```

---

## Where to submit

| Directory | Mechanism | Action |
|---|---|---|
| **Official MCP Registry** | `mcp-publisher` (automated in CI) | ✅ Done — auto-publishes on each `v*` tag |
| **PulseMCP** (~16k) | Ingests official registry + manual Submit | Likely auto-listed over time; to expedite, use the **Submit** button at https://www.pulsemcp.com |
| **Glama** (~25k) | Form, manually reviewed; also indexes GitHub | Submit the repo URL at https://glama.ai/mcp/servers |
| **mcp.so** | GitHub issue / Submit button | Submit at https://mcp.so (Submit in nav) — paste metadata + Claude Desktop snippet |
| **Awesome MCP Servers** | PR to GitHub list / form | See the entry draft below; submit at https://mcpservers.org/submit or PR to `punkpeye/awesome-mcp-servers` |
| **MCP Server Hub** | Form | https://mcpserverhub.net/submit |
| **Smithery** | Hosted HTTP URL only | **Not pursued.** Smithery now requires a URL to a *running* HTTP MCP server ("Smithery requires a URL to a running server, not a GitHub repository"); it no longer lists stdio/GitHub-repo servers. supertone-mcp is local stdio (no hosted endpoint), and a hosted instance would need its own API-key/cost model. Revisit only if we deploy a Streamable-HTTP server. |

> Tip: aggregators scrape the official registry on an infrequent schedule
> (≈hourly+) and keep their own index, so propagation is not instant.
> Manual submission is the fastest way onto a specific directory.

---

## Awesome MCP Servers — entry draft

Target category: **Text-to-Speech / Audio** (or the closest audio/voice section).
Format follows `punkpeye/awesome-mcp-servers` (🐍 Python · 🏠 local service):

```markdown
- [supertone-inc/supertone-mcp](https://github.com/supertone-inc/supertone-mcp) 🐍 🏠 - High-quality Supertone TTS: voice search & preview, duration prediction, and voice cloning (Korean/English/Japanese).
```
