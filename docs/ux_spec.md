# UX Specification: Supertone TTS MCP Server

> Generated: 2026-03-13 (v0.1) / 2026-05-26 (v0.2 extension)
> Source: PRD v0.2, Requirements v0.2
> Author: ux-designer agent

> **v0.2 changes**
> - `list_voices` is REMOVED (breaking change) and replaced by `search_voice`.
> - New tools (see §2.3+): `search_voice`, `get_voice`, `get_credit_balance`, `preview_voice`, `predict_duration`, `clone_voice`, `search_custom_voice`, `edit_custom_voice`, `delete_custom_voice`.
> - All v0.1 sections below referring to `list_voices` describe historical behavior and are retained for traceability; the active tool surface is the v0.2 set.

---

## 1. Information Architecture

This MCP server exposes exactly two tools. The tool surface is intentionally minimal -- users interact through natural language in their MCP client (Claude Desktop, Cursor), and the LLM translates intent into tool calls.

### Tool Hierarchy (v0.2)

```
supertone-tts (MCP Server)
|
+-- TTS
|   +-- text_to_speech       Primary action tool. Converts text to audio file.
|   +-- predict_duration     Predicts output audio length without synthesizing.
|
+-- Voice discovery
|   +-- search_voice         Filtered voice catalog query (replaces list_voices).
|   +-- get_voice            Single voice detail by voice_id.
|   +-- preview_voice        Sample audio URLs for a voice (no autoplay in v0.2).
|
+-- Account
|   +-- get_credit_balance   Remaining credits.
|
+-- Voice cloning (custom voices)
    +-- clone_voice          Create a cloned voice from a local audio file (≤3MB, wav/mp3).
    +-- search_custom_voice  List user's own custom voices.
    +-- edit_custom_voice    Rename or update description of a custom voice.
    +-- delete_custom_voice  Permanently delete a custom voice (irreversible).
```

> Note: v0.1 had only `text_to_speech` and `list_voices`. v0.2 removes `list_voices` (breaking change) and adds nine new tools (one replacement + eight new).

### Design Principles

1. **Discoverability through naming:** Tool names use snake_case and describe the action (`text_to_speech`, `clone_voice`) or the query (`search_voice`, `get_credit_balance`). No abbreviations, no brand prefixes on tool names.
2. **Progressive disclosure:** Only `text` is required for `text_to_speech`. All other parameters have sensible defaults. Users can start simple and add specificity as needed.
3. **Tool descriptions drive LLM behavior:** The MCP tool schema descriptions are the primary "UI" -- they tell the LLM when and how to invoke each tool. Descriptions must be precise and concise.

---

## 2. Tool Schema Descriptions (Copy Guidelines)

Tool descriptions are the most important UX surface. They are read by the LLM to decide when to call the tool and how to fill parameters. They must be:

- **Accurate:** Do not overstate capabilities.
- **Actionable:** Tell the LLM what the tool does and what it returns.
- **Concise:** LLM context is expensive. No filler words.

### 2.1 `text_to_speech`

**Tool description:**
```
Convert text to speech using Supertone TTS API. Saves the audio file locally and returns the file path and duration. Supports Korean, English, and Japanese. Maximum 300 characters per call.
```

**Parameter descriptions:**

| Parameter | Description |
|-----------|-------------|
| `text` | Text to convert to speech. Required. Maximum 300 characters. |
| `voice_id` | Voice identifier. Use search_voice (v0.2) to discover available options. If omitted, a default Korean voice is used. |
| `language` | Language code: "ko" (Korean, default), "en" (English), or "ja" (Japanese). |
| `output_format` | Audio format: "mp3" (default) or "wav". |
| `speed` | Playback speed multiplier. Range: 0.5 to 2.0. Default: 1.0. |
| `pitch_shift` | Pitch adjustment in semitones. Range: -12 to +12. Default: 0. |
| `style` | Emotion style (e.g., "neutral", "happy"). Available styles vary by voice -- use search_voice or get_voice (v0.2) to check. |

### 2.2 `list_voices` — **REMOVED in v0.2**

Replaced by `search_voice` (§2.3). v0.1 description retained for historical traceability only:

> **(v0.1, removed):** "List available Supertone TTS voices. Returns voice ID, name, supported languages, and supported emotion styles for each voice. Optionally filter by language."
> **Migration:** Pass no arguments to `search_voice` to reproduce the old behavior; use the additional filter parameters for richer queries.

### 2.3 `search_voice` (v0.2)

**Tool description:**
```
Search the Supertone voice catalog. Filters are optional and combined with AND semantics: name, description, language, gender, age, use_case, style, model. With no filters, returns the full catalog (the v0.1 list_voices behavior). The output is a numbered plain-text list; when any filter is set, the first line shows "Filters applied: ...".
```

**Parameter descriptions:**

| Parameter | Description |
|-----------|-------------|
| `name` | Voice name (partial match). |
| `description` | Voice description (partial match). |
| `language` | Language code (e.g., "ko", "en", "ja"). |
| `gender` | Voice gender (e.g., "male", "female"). |
| `age` | Age bracket (e.g., "young_adult", "child"). |
| `use_case` | Single use case keyword (e.g., "narration", "advertisement"). |
| `style` | Emotion style (e.g., "neutral", "happy"). |
| `model` | TTS model identifier (e.g., "sona_speech_1"). |

### 2.4 `get_voice` (v0.2)

**Tool description:**
```
Fetch full detail for a single voice by voice_id. Returns name, description, age, gender, use_cases, languages, styles, supported models, sample count, and thumbnail URL. Use preview_voice to get the actual sample audio URLs.
```

**Parameter descriptions:**

| Parameter | Description |
|-----------|-------------|
| `voice_id` | Voice identifier returned by search_voice. Required. |

### 2.5 `get_credit_balance` (v0.2)

**Tool description:**
```
Returns the remaining Supertone credit balance for the current API key. Use this before long TTS calls to confirm you have enough characters left.
```

**Parameter descriptions:** _none_

### 2.6 `preview_voice` (v0.2)

**Tool description:**
```
Fetch sample audio URLs for a voice. Optionally filter samples by language, style, and model. Returns one URL per matching sample. v0.2 does NOT play the audio locally; pass the URL to your client to listen.
```

**Parameter descriptions:**

| Parameter | Description |
|-----------|-------------|
| `voice_id` | Voice identifier. Required. |
| `language` | Filter samples by language code. |
| `style` | Filter samples by emotion style. |
| `model` | Filter samples by TTS model identifier. |

### 2.7 `predict_duration` (v0.2)

**Tool description:**
```
Predict the expected output audio length (seconds) for a given text WITHOUT producing any audio file. Accepts the same parameters as text_to_speech and applies the same 300-character limit. Use this to estimate credit cost before synthesizing.
```

**Parameter descriptions:** Same as `text_to_speech` (see §2.1). No `voice_id` defaulting differences. No file is saved.

### 2.8 `clone_voice` (v0.2)

**Tool description:**
```
Create a custom voice from a single local audio file. Constraints: WAV or MP3 only, max 3MB, exactly one file. The returned voice_id can be used immediately in text_to_speech. Path supports ~ expansion (e.g., "~/sample.wav").
```

**Parameter descriptions:**

| Parameter | Description |
|-----------|-------------|
| `name` | Display name for the new voice. Required, non-empty. |
| `audio_path` | Absolute or ~-prefixed local path to a WAV or MP3 file (≤ 3MB). Required. |
| `description` | Optional note/description for the new voice. |

### 2.9 `search_custom_voice` (v0.2)

**Tool description:**
```
List custom (cloned) voices created by this API key. Optional name and description filters perform partial matching. Pagination is handled internally; v0.2 returns the SDK default page.
```

**Parameter descriptions:**

| Parameter | Description |
|-----------|-------------|
| `name` | Partial-match filter on custom voice name. |
| `description` | Partial-match filter on custom voice description. |

### 2.10 `edit_custom_voice` (v0.2)

**Tool description:**
```
Update the name and/or description of an existing custom voice. At least one of name or description must be provided.
```

**Parameter descriptions:**

| Parameter | Description |
|-----------|-------------|
| `voice_id` | Custom voice identifier. Required. |
| `name` | New name. Optional, but one of name/description must be set. |
| `description` | New description. Optional, but one of name/description must be set. |

### 2.11 `delete_custom_voice` (v0.2)

**Tool description:**
```
Permanently delete a custom (cloned) voice. THIS IS IRREVERSIBLE — once deleted, the voice cannot be recovered and any saved voice_id referencing it will stop working. Confirm with the user before calling.
```

**Parameter descriptions:**

| Parameter | Description |
|-----------|-------------|
| `voice_id` | Custom voice identifier to delete. Required. |

---

## 3. Key Interaction Flows

### 3.1 Text-to-Speech Flow (Happy Path)

```
User (in Claude Desktop): "Read this sentence aloud: Hello, how are you?"
  |
  v
LLM decides to call text_to_speech(text="Hello, how are you?", language="en")
  |
  v
MCP Server:
  1. Validate parameters (text length, language code, ranges)
  2. Resolve voice_id (use default if not provided)
  3. Call Supertone API: POST /v1/text-to-speech/{voice_id}
  4. Save audio stream to file: ~/supertone-tts-output/2026-03-13_a1b2c3.mp3
  5. Return success response
  |
  v
LLM presents to user:
  "I've generated the audio file. It's saved at:
   ~/supertone-tts-output/2026-03-13_a1b2c3.mp3 (duration: 2.3 seconds)"
```

### 3.2 List Voices Flow (Happy Path)

```
User: "What voices are available for Japanese?"
  |
  v
LLM calls list_voices(language="ja")
  |
  v
MCP Server:
  1. Validate language parameter
  2. Call Supertone API: GET /v1/voices
  3. Filter results by language
  4. Return structured voice list
  |
  v
LLM presents to user:
  "Here are the available Japanese voices:
   - Yuki (voice_id: yuki-01) -- styles: neutral, happy, sad
   - Kenji (voice_id: kenji-01) -- styles: neutral, serious"
```

### 3.3 Error Paths

Each error path follows a consistent structure: **what went wrong** + **what to do about it**.

```
Error Flow: API Key Missing
  User calls any tool
    -> Server checks SUPERTONE_API_KEY env var
    -> Not set or empty
    -> Return error (no API call made)

Error Flow: Text Too Long
  User calls text_to_speech with 350 characters
    -> Server validates text length
    -> Exceeds 300 chars
    -> Return error (no API call made)

Error Flow: Invalid Parameter
  User calls text_to_speech(speed=5.0)
    -> Server validates speed range
    -> Out of range [0.5, 2.0]
    -> Return error (no API call made)

Error Flow: API Authentication Failure
  User calls tool with invalid API key
    -> Server calls Supertone API
    -> API returns HTTP 401/403
    -> Return error with auth guidance

Error Flow: API Rate Limit
  User calls tool too frequently
    -> API returns HTTP 429
    -> Return error with wait guidance

Error Flow: Network Failure
  User calls tool, network is down
    -> httpx raises connection error or timeout
    -> Return error with network guidance

Error Flow: File System Permission Error
  Server cannot write to output directory
    -> OS raises PermissionError
    -> Return error with directory guidance
```

---

## 4. Tool States (Input/Output Specification)

### 4.1 `text_to_speech`

#### Success State

**Input example:**
```json
{
  "text": "Hello, this is a test.",
  "language": "en",
  "output_format": "mp3",
  "speed": 1.0
}
```

**Output format:**
```
Audio file saved: /Users/username/supertone-tts-output/2026-03-13_a1b2c3.mp3
Duration: 2.3 seconds
Voice: yuki-01
Language: en
Format: mp3
```

The output is plain text, not JSON. MCP tool responses are consumed by the LLM, which will reformat for the user. Structured but human-readable text is the optimal format -- it is easy for the LLM to parse and present.

#### Error States

| Error Condition | Output Message |
|----------------|----------------|
| API key not set | `SUPERTONE_API_KEY environment variable is not set. Please configure it in your MCP client settings.` |
| Empty text | `Text must not be empty.` |
| Text too long | `Text exceeds the maximum length of 300 characters (received: {N}). Please shorten or split the text manually.` |
| Invalid language | `Invalid language: "{value}". Supported languages: ko, en, ja.` |
| Invalid output_format | `Invalid output format: "{value}". Supported formats: mp3, wav.` |
| Speed out of range | `Speed must be between 0.5 and 2.0 (received: {value}).` |
| Pitch out of range | `Pitch shift must be between -12 and +12 semitones (received: {value}).` |
| Invalid style | `Style "{value}" is not supported by voice "{voice_id}". Available styles: {list}.` |
| API auth failure (401/403) | `Authentication failed. Please verify your SUPERTONE_API_KEY.` |
| Rate limit (429) | `Rate limit exceeded. Please wait and try again.` |
| API server error (5xx) | `Supertone API server error ({status_code}). Please try again later.` |
| Network/connection error | `Failed to connect to Supertone API. Please check your network connection.` |
| Output dir permission error | `Cannot write to output directory: {path}. Please check directory permissions or set SUPERTONE_OUTPUT_DIR to a writable location.` |

#### Edge Cases

| Case | Behavior |
|------|----------|
| Exactly 300 characters | Accepted. Proceeds normally. |
| 301 characters | Rejected with text-too-long error. |
| Unicode text (e.g., Korean, emoji) | Character count uses Python `len()` (counts Unicode codepoints, not bytes). |
| `voice_id` not provided | Default voice is used. Success message includes the default voice_id for transparency. |
| `style` not provided | Voice's default style is used. Not mentioned in output unless explicitly set. |
| Output directory does not exist | Created automatically (including intermediate directories). |
| File name collision | Unique ID component prevents collisions. File naming: `{YYYY-MM-DD}_{uuid_short}.{format}`. |

### 4.2 `list_voices`

#### Success State (with results)

**Input example:**
```json
{
  "language": "ko"
}
```

**Output format:**
```
Found 3 voices matching language: ko

1. Name: Sujin
   Voice ID: sujin-01
   Languages: ko, en
   Styles: neutral, happy, sad, angry

2. Name: Minho
   Voice ID: minho-01
   Languages: ko
   Styles: neutral, serious

3. Name: Yuna
   Voice ID: yuna-01
   Languages: ko, ja
   Styles: neutral, happy
```

Output uses a numbered list format. Each voice entry is separated by a blank line for readability. Fields are labeled clearly so the LLM can extract and present them in any format (table, list, prose).

#### Success State (empty results)

**Input example:**
```json
{
  "language": "ja"
}
```

**Output (when no Japanese voices exist):**
```
No voices found matching language: ja.
```

This is a success state, not an error. The query succeeded but returned no results.

#### Success State (no filter)

**Input example:**
```json
{}
```

**Output:**
```
Found 5 voices:

1. Name: Sujin
   ...
```

#### Error States

| Error Condition | Output Message |
|----------------|----------------|
| API key not set | `SUPERTONE_API_KEY environment variable is not set. Please configure it in your MCP client settings.` |
| Invalid language filter | `Invalid language filter: "{value}". Supported languages: ko, en, ja.` |
| API auth failure (401/403) | `Authentication failed. Please verify your SUPERTONE_API_KEY.` |
| Rate limit (429) | `Rate limit exceeded. Please wait and try again.` |
| API server error (5xx) | `Supertone API server error ({status_code}). Please try again later.` |
| Network/connection error | `Failed to connect to Supertone API. Please check your network connection.` |

> Section 4.2 documents the historical v0.1 `list_voices` behavior. v0.2 callers should use `search_voice` (§4.3).

### 4.3 `search_voice` (v0.2)

#### Success State (with results, filters applied)

**Input example:** `{"language": "ko", "gender": "female"}`

**Output format:**
```
Filters applied: language=ko, gender=female
Found 2 voices:

1. Name: Sujin
   Voice ID: sujin-01
   Languages: ko, en
   Styles: neutral, happy, sad

2. Name: Yuna
   Voice ID: yuna-01
   Languages: ko, ja
   Styles: neutral, happy
```

#### Success State (no filters)

**Input example:** `{}`

**Output:** Same numbered list as above WITHOUT the `Filters applied:` line. First line is `Found N voices:`.

#### Success State (zero results)

**Output:** `No voices found matching the filters.`

#### Error States

| Error Condition | Output Message |
|----------------|----------------|
| API key not set | `SUPERTONE_API_KEY environment variable is not set. Please configure it in your MCP client settings.` |
| API auth failure (401/403) | `Authentication failed. Please verify your SUPERTONE_API_KEY.` |
| Rate limit (429) | `Rate limit exceeded. Please wait and try again.` |
| API server error (5xx) | `Supertone API server error ({status_code}). Please try again later.` |
| Network error | `Failed to connect to Supertone API. Please check your network connection.` |

### 4.4 `get_voice` (v0.2)

#### Success State

**Input example:** `{"voice_id": "sujin-01"}`

**Output format:**
```
Voice ID: sujin-01
Name: Sujin
Description: A warm, professional female voice suited for narration.
Age: young_adult
Gender: female
Use cases: narration, advertisement
Languages: ko, en
Styles: neutral, happy, sad
Models: sona_speech_1
Samples: 6
Thumbnail: https://.../sujin-01.png

Use preview_voice to fetch sample URLs.
```

#### Error States

| Error Condition | Output Message |
|----------------|----------------|
| `voice_id` empty | `voice_id must not be empty.` |
| Voice not found (404) | `Voice not found: "{voice_id}".` |
| API key not set / auth / rate / 5xx / network | Same as §4.3. |

### 4.5 `get_credit_balance` (v0.2)

#### Success State (minimal)

**Output:** `Credit balance: 12345 credits remaining.`

#### Success State (with plan & expiry)

**Output:**
```
Credit balance: 12345 credits remaining.
Plan: pro
Expires: 2026-12-31
```

#### Error States

| Error Condition | Output Message |
|----------------|----------------|
| API key not set / auth / rate / 5xx / network | Same as §4.3. |

### 4.6 `preview_voice` (v0.2)

#### Success State

**Input example:** `{"voice_id": "sujin-01", "language": "ko"}`

**Output format:**
```
1. [language=ko, style=happy, model=sona_speech_1] https://.../sujin-happy.wav
2. [language=ko, style=neutral, model=sona_speech_1] https://.../sujin-neutral.wav
```

#### Edge States

| Condition | Output |
|----------|--------|
| Voice has zero samples | `This voice has no preview samples.` |
| Filters match no samples | `No matching samples for the given filters.` |

#### Error States

| Error Condition | Output Message |
|----------------|----------------|
| `voice_id` empty | `voice_id must not be empty.` |
| Voice not found (404) | `Voice not found: "{voice_id}".` |
| API key / auth / rate / 5xx / network | Same as §4.3. |

### 4.7 `predict_duration` (v0.2)

#### Success State

**Input example:**
```json
{"text": "Hello, this is a test.", "language": "en"}
```

**Output format:**
```
Predicted duration: 2.34s (credit usage is proportional to duration).
```

#### Error States

Validation messages are identical to `text_to_speech` (§4.1):

| Error Condition | Output Message |
|----------------|----------------|
| Empty text | `Text must not be empty.` |
| Text > 300 chars | `Text exceeds the maximum length of 300 characters (received: {N}). Please shorten or split the text manually.` |
| Invalid language | `Invalid language: "{value}". Supported languages: ko, en, ja.` |
| Invalid output_format | `Invalid output format: "{value}". Supported formats: mp3, wav.` |
| Speed out of range | `Speed must be between 0.5 and 2.0 (received: {value}).` |
| Pitch out of range | `Pitch shift must be between -12 and +12 semitones (received: {value}).` |
| API key / auth / rate / 5xx / network | Same as §4.1. |

### 4.8 `clone_voice` (v0.2)

#### Success State

**Input example:**
```json
{"name": "MyVoice", "audio_path": "~/samples/my-voice.wav", "description": "warm narration voice"}
```

**Output format:**
```
Custom voice created. voice_id: cv_abc123. Use this voice_id in text_to_speech.
```

#### Edge cases

- `~` in `audio_path` is expanded to the user's home directory.
- All file validation happens BEFORE any API call (fail-fast):
  - existence → extension → size → name non-empty.

#### Error States

| Error Condition | Output Message |
|----------------|----------------|
| File missing | `Audio file not found: {path}.` |
| Wrong extension | `Unsupported audio format: "{ext}". Supported: wav, mp3.` |
| File > 3MB | `Audio file exceeds the 3MB limit (received: {N} bytes).` |
| Empty `name` | `Voice name must not be empty.` |
| Read permission denied | `Cannot read audio file: {path}. Please check file permissions.` |
| API key / auth / rate / 5xx / network | Same as §4.3. |

### 4.9 `search_custom_voice` (v0.2)

#### Success State (with results)

**Output:**
```
Found 2 custom voices:

1. Name: MyVoice
   Voice ID: cv_abc123
   Description: warm narration voice
   Created: 2026-05-26

2. Name: PodcastIntro
   Voice ID: cv_def456
   Description: -
   Created: 2026-05-20
```

#### Success State (zero results)

**Output:** `No custom voices found.`

#### Error States

| Error Condition | Output Message |
|----------------|----------------|
| API key / auth / rate / 5xx / network | Same as §4.3. |

### 4.10 `edit_custom_voice` (v0.2)

#### Success State

**Input example:** `{"voice_id": "cv_abc123", "name": "MyVoice (v2)"}`

**Output:** `Custom voice updated. voice_id: cv_abc123.`

#### Error States

| Error Condition | Output Message |
|----------------|----------------|
| Neither `name` nor `description` provided | `At least one of name or description must be provided.` |
| `voice_id` empty | `voice_id must not be empty.` |
| Custom voice not found (404) | `Custom voice not found: "{voice_id}".` |
| API key / auth / rate / 5xx / network | Same as §4.3. |

### 4.11 `delete_custom_voice` (v0.2)

#### Success State

**Input example:** `{"voice_id": "cv_abc123"}`

**Output:** `Custom voice deleted. voice_id: cv_abc123.`

> **Important UX note:** v0.2 does NOT implement a confirmation gate inside the tool. The LLM is expected to relay the irreversibility warning from the tool description text to the user. If product feedback suggests this is insufficient, a confirm gate may be added in v0.3.

#### Error States

| Error Condition | Output Message |
|----------------|----------------|
| `voice_id` empty | `voice_id must not be empty.` |
| Custom voice not found (404) | `Custom voice not found: "{voice_id}".` |
| API key / auth / rate / 5xx / network | Same as §4.3. |

---

## 5. Error Message Copy Guidelines

### 5.1 Structure

Every error message must follow this template:

```
{What went wrong}. {What the user should do}.
```

Examples:
- "Text exceeds the maximum length of 300 characters (received: 412). Please shorten or split the text manually."
- "Authentication failed. Please verify your SUPERTONE_API_KEY."

### 5.2 Rules

1. **No stack traces.** Never expose Python tracebacks, internal module names, or line numbers in tool responses.
2. **No API key echo.** Never include the API key value (even partially) in any output.
3. **Specific over generic.** "Speed must be between 0.5 and 2.0 (received: 5.0)" is better than "Invalid parameter."
4. **Include received values.** When a user provides an invalid value, echo it back so they can see the mistake. Exception: never echo the API key.
5. **Suggest the fix.** Every error message ends with guidance. If the fix requires configuration, name the specific environment variable or setting.
6. **Use plain English.** Avoid jargon like "HTTP 401" in user-facing messages. Map status codes to human-readable descriptions. Exception: 5xx errors include the status code because it aids debugging with Supertone support.
7. **Consistent tone.** Neutral and direct. No apologies ("Sorry, ..."), no exclamation marks, no emoji.
8. **Period-terminated.** Every message ends with a period.

### 5.3 Language

All error messages and tool descriptions are in **English**. The tool converts text in multiple languages but its own interface is English-only. This is consistent with MCP ecosystem conventions and the target audience (developers).

---

## 6. Output Formatting and Accessibility

### 6.1 Plain Text Output

All tool responses use plain text, not JSON or Markdown. Rationale:
- MCP tool responses are consumed by the LLM, which reformats for presentation.
- Plain text is universally parseable by any LLM.
- Structured text (labeled fields, numbered lists) gives the LLM enough structure to present well.

### 6.2 File Paths

- Always return **absolute paths** (e.g., `/Users/username/supertone-tts-output/...`), not relative paths or paths with `~`.
- Expand `~` to the full home directory path before returning.
- Use forward slashes on all platforms for consistency in the returned message.

### 6.3 Numbers

- Duration: always include unit ("2.3 seconds", not "2.3s" or "2.3").
- Speed/pitch: include the unit or context in error messages ("0.5 to 2.0", "-12 to +12 semitones").

### 6.4 Lists

- Use numbered lists for voice listings (aids reference: "use voice number 2").
- Use labeled fields within each list item (not positional).
- Separate list items with blank lines for readability.

### 6.5 Consistency

- Field labels use Title Case followed by a colon: "Voice ID:", "Languages:", "Styles:".
- Enum values (language codes, format names) are always lowercase in output: `ko`, `mp3`.
- Voice names use their original casing from the API.

---

## 7. Interaction Edge Cases and Guidance

### 7.1 LLM-Mediated Interactions

Users do not call MCP tools directly -- the LLM decides when and how to invoke them. This means:

- **The LLM may call `search_voice` (or `get_voice` + `preview_voice`) before `text_to_speech`** to help the user choose a voice. The tool descriptions should encourage this pattern (the `voice_id` description says "Use search_voice to see available options").
- **The LLM may call `predict_duration` and/or `get_credit_balance` before `text_to_speech`** when the text is long, to forewarn the user of credit cost.
- **The LLM should always warn the user before calling `delete_custom_voice`** — the tool description marks it as irreversible and v0.2 has no confirmation gate.
- **The LLM may adjust parameters** based on user intent. For example, if a user says "make it faster," the LLM may call `text_to_speech` with `speed=1.5`.
- **The LLM will present errors** in natural language. Error messages should be written so they can be relayed directly to the user without reformulation.

### 7.2 Multi-Turn Patterns

Common multi-turn flows the tool descriptions should support:

1. **Explore then generate (v0.2):** User asks "find me a warm Korean female voice" -> LLM calls `search_voice(language="ko", gender="female")` -> User says "show me sample 1" -> LLM calls `preview_voice(voice_id=...)` -> User confirms -> LLM calls `text_to_speech` with that `voice_id`.
2. **Iterate on parameters:** User says "make it slower" -> LLM calls `text_to_speech` again with lower `speed`, keeping other params.
3. **Language switch:** User says "now say the same thing in Japanese" -> LLM calls `text_to_speech` with `language="ja"` and the same text.
4. **Budget check (v0.2):** User asks "synthesize this 300-character paragraph" -> LLM calls `get_credit_balance` then `predict_duration` -> Reports estimated duration & credit usage -> User approves -> LLM calls `text_to_speech`.
5. **Voice cloning lifecycle (v0.2):** User says "clone this audio as MyVoice" -> LLM calls `clone_voice` -> Later "rename MyVoice to PodcastVoice" -> LLM calls `edit_custom_voice` -> Eventually "delete PodcastVoice" -> LLM warns it's irreversible, gets user confirmation, then calls `delete_custom_voice`.

The tool itself is stateless -- it does not remember previous calls. The LLM maintains conversational context.

### 7.3 What the Server Does NOT Do

- **No audio playback.** The server saves a file and returns the path (for `text_to_speech`) or sample URLs (for `preview_voice`). Local playback is the client's responsibility; an explicit `play_audio_url` tool is deferred to v0.3.
- **No text splitting.** If text exceeds 300 characters, the user (or LLM) must split it manually.
- **No voice recommendation.** The server does not suggest voices. The LLM can use `search_voice` output to make suggestions.
- **No multi-file voice cloning.** v0.2 accepts exactly one audio file per `clone_voice` call. Multi-sample cloning is deferred to v0.3.
- **No delete confirmation gate.** `delete_custom_voice` runs immediately. The LLM is expected to confirm with the user (the tool description marks the action as irreversible).
- **No progress indication.** MCP tool calls are synchronous from the client's perspective. There is no streaming progress update. The Supertone API response time (typically 1-5 seconds) is the dominant wait.

---

## 8. Traceability

| UX Element | Requirement |
|-----------|-------------|
| `text_to_speech` tool description | FR-001, US-001 |
| `list_voices` tool description (v0.1, removed) | FR-002 (removed), US-002 (superseded) |
| `search_voice` tool description & filters | FR-012, US-007, US-008 |
| `get_voice` tool description | FR-013, US-008 |
| `get_credit_balance` tool description | FR-014, US-009 |
| `preview_voice` tool description | FR-015, US-008 |
| `predict_duration` tool description & validation reuse | FR-016, US-010 |
| `clone_voice` tool description & file constraints | FR-017, US-011 |
| `search_custom_voice` tool description | FR-018, US-011 |
| `edit_custom_voice` tool description & at-least-one rule | FR-019, US-011 |
| `delete_custom_voice` tool description (irreversibility warning) | FR-019, US-011, NFR-004 |
| Language parameter copy | US-003, FR-006 |
| Speed/pitch parameter copy | US-004, FR-006 |
| Style parameter copy | US-005, FR-006 |
| Output format parameter copy | US-006, FR-006 |
| Language filter in search_voice | US-007, FR-012 |
| API key error message | FR-003, NFR-004, NFR-007 |
| Text length error message | FR-005, NFR-004 |
| Parameter validation errors | FR-006, NFR-004 |
| API error messages (401, 429, 5xx, network) | FR-007, NFR-004 |
| Output directory error message | FR-004, NFR-004 |
| Absolute file path in output | FR-001 |
| Plain text output format | NFR-004 (clarity) |
