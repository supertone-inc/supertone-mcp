# PRD: Supertone MCP Server

> Status: Draft
> Version: v0.3 (concept pivot — composable SDK toolkit)
> Date: 2026-06-05
> Author: pillip

---

## 1. Background

MCP(Model Context Protocol)는 LLM 클라이언트(Claude Desktop, Cursor, OpenClaw 등)에서 외부 도구를 연동하는 표준 프로토콜로, 2024년 11월 출시 이후 폭발적으로 성장 중이다(10,000+ 서버, 5개월간 다운로드 80배 증가).

수퍼톤(Supertone)은 HYBE 자회사로 한국어 특화 고품질 TTS를 제공하며, API를 통해 23개 언어의 음성 합성을 지원한다. 현재 MCP 생태계에 TTS 서버는 5개 이상 존재하나, **수퍼톤 기반 MCP 서버는 없다.**

이 프로젝트는 수퍼톤 TTS API를 MCP 서버로 래핑하여 배포함으로써:
1. MCP 서버 개발 기술을 습득하고
2. 수퍼톤 API 사용량을 간접적으로 증가시키는 것을 목표로 한다.

### v0.3 컨셉 전환 (Concept Pivot)

v0.1~v0.2는 **"LLM이 생성한 텍스트를 음성으로 변환해 사용자에게 들려주는 것"**(TTS 중심, 결과 오디오를 사용자에게 재생)에 초점을 두었다.

v0.3부터는 컨셉을 전환한다: **수퍼톤 SDK가 제공하는 기능을 그대로 충실하게 MCP tool로 노출**하여, LLM이 이 tool들을 **레고 블록처럼 조립(compose)**해 사용자에게 결과를 돌려줄 수 있게 한다.

이 전환의 핵심 원칙:

1. **동작은 환경변수가 아니라 tool 파라미터로 결정한다.** 서버를 재시작하지 않고도 LLM이 호출마다 동작을 선택할 수 있어야 진정한 "조립"이 가능하다.
2. **숨은 부수효과(hidden side-effect)를 제거한다.** "사용자에게 자동 재생" 같은 행위는 LLM이 의도적으로 선택해야 하는 것이지, 서버 설정으로 강제되어선 안 된다.
3. **SDK 표면을 충실히(faithfully) 반영한다.** tool은 SDK 기능을 가공·은폐하지 않고 1:1로 매핑하되, LLM이 다루기 쉬운 형태로 입출력을 정돈한다.

따라서 다음 환경변수 기반 **동작 제어 스위치를 제거**하고 tool 파라미터로 옮긴다:
- `SUPERTONE_MCP_OUTPUT_MODE` → `text_to_speech`의 per-call `output_mode` 파라미터 (`files` / `resources` / `both`)
- `SUPERTONE_MCP_AUTOPLAY` → `text_to_speech`의 per-call `autoplay` 파라미터

(인증 `SUPERTONE_API_KEY`, 기본값 `SUPERTONE_MCP_VOICE_ID`·`SUPERTONE_OUTPUT_DIR`는 *동작 스위치*가 아니라 *기본값/설정*이므로 환경변수로 유지한다.)

---

## 2. Goals

| # | 목표 | 측정 기준 |
|---|------|----------|
| G1 | MCP 서버 개발 역량 확보 | MCP 표준을 준수하는 동작하는 서버 완성 |
| G2 | 수퍼톤 TTS를 MCP 생태계에 진입시킴 | Claude Desktop + Cursor에서 정상 동작 확인 |
| G3 | 오픈소스로 배포하여 외부 사용자 확보 | GitHub 공개 + PyPI 배포 |
| G4 | **SDK를 조립 가능한 tool 세트로 노출** | 동작 제어 환경변수 0개(인증·기본값 제외), 모든 tool 동작을 호출 파라미터로 결정 가능 |

---

## 3. Non-Goals (Out of Scope)

- STT(Speech-to-Text) 기능 — MCP의 구조(LLM이 tool 호출)와 맞지 않음
- 음성 대화 인터페이스 (STT→LLM→TTS) — 별도 프로젝트로 분리
- 배치 변환(batch TTS) — v3에서 고려
- 다중 파일 voice clone (멀티샘플 업로드) — v3에서 고려 (v0.2는 단일 파일만)
- `preview_voice`의 로컬 자동 재생 — `preview_voice`는 URL만 반환한다. (단, `text_to_speech`는 v0.3부터 per-call `autoplay` 파라미터를 지원한다 — 아래 FR1 참고)
- 모델 목록 조회 (`list_models`) — v3에서 고려 (현재는 SDK 기본값 사용)
- ~~단일 custom voice 조회 (`get_custom_voice`)~~ — **v0.3에서 노출** (SDK 0.2.3이 `get_custom_voice_async` 제공, FR-020)
- 삭제 확인 게이트 (delete confirm prompt) — v0.2는 tool 설명 경고만으로 충분
- 웹 UI 또는 별도 클라이언트 앱
- 수퍼톤 외 다른 TTS 엔진 지원

---

## 4. Target Users

### Primary: MCP 사용자 (개발자/크리에이터)
- Claude Desktop, Cursor, OpenClaw 등 MCP 지원 클라이언트를 사용하는 사람
- LLM이 수퍼톤 tool들을 조립해 음성 워크플로우를 자율적으로 수행하길 원하는 경우
- 예: "happy 스타일 한국어 보이스를 골라서, 예상 길이를 먼저 확인하고, 이 문장을 mp3 리소스로만 합성해줘" — LLM이 `search_voice` → `predict_duration` → `text_to_speech(output_mode='resources')`를 순서대로 조립
- 예: "내 목소리로 보이스를 만들고, 그 보이스로 이 인삿말을 합성한 다음 바로 재생해줘" — `clone_voice` → `text_to_speech(autoplay=true)`

### Secondary: 콘텐츠 크리에이터
- 나레이션, 더빙 등을 LLM 워크플로우 안에서 자동화하고 싶은 사람
- 한국어 고품질 음성이 필요한 사람

---

## 5. User Stories

| # | 스토리 | 우선순위 |
|---|--------|---------|
| US1 | MCP 사용자로서, 텍스트를 입력하면 수퍼톤 TTS로 음성 파일을 생성하고 싶다. 그래야 타이핑한 내용을 음성으로 들을 수 있다. | Must |
| US2 | MCP 사용자로서, 사용 가능한 보이스 목록을 조회하고 싶다. 그래야 원하는 목소리를 골라서 TTS에 사용할 수 있다. | Must |
| US3 | MCP 사용자로서, 음성의 언어(한/영/일)를 지정하고 싶다. 그래야 다국어 콘텐츠를 만들 수 있다. | Must |
| US4 | MCP 사용자로서, 음성의 속도와 피치를 조절하고 싶다. 그래야 용도에 맞는 음성을 만들 수 있다. | Should |
| US5 | MCP 사용자로서, 감정 스타일(neutral, happy 등)을 지정하고 싶다. 그래야 표현력 있는 음성을 만들 수 있다. | Should |
| US6 | MCP 사용자로서, 출력 포맷(wav/mp3)을 선택하고 싶다. 그래야 용도에 맞는 파일을 받을 수 있다. | Should |
| US7 | MCP 사용자로서, 보이스 목록을 언어로 필터링하고 싶다. 그래야 내가 원하는 언어의 보이스만 본다. | Should |
| US8 | MCP 사용자로서, 이름·성별·나이·use_case·style 등 다양한 조건으로 보이스를 검색하고, 샘플 오디오를 미리 들어볼 수 있는 URL을 받고 싶다. 그래야 TTS에 사용할 보이스를 자신 있게 고를 수 있다. | Must |
| US9 | MCP 사용자로서, TTS 호출 전에 남은 크레딧을 확인하고 싶다. 그래야 긴 텍스트를 합성하기 전에 비용 부담을 가늠할 수 있다. | Must |
| US10 | MCP 사용자로서, 텍스트를 합성하기 전에 결과 음성의 예상 길이(초)를 알고 싶다. 그래야 콘텐츠 길이를 미리 설계할 수 있다. | Must |
| US11 | MCP 사용자로서, 내 목소리(또는 보유한 음성 샘플)로 커스텀 보이스를 만들고, 만든 보이스를 검색·수정·삭제할 수 있어야 한다. 그래야 나만의 보이스로 콘텐츠를 만들 수 있다. | Must |
| US12 | MCP 사용자(LLM)로서, 매 호출마다 음성 결과의 반환 방식(파일 저장 / MCP 리소스 / 둘 다)을 선택하고 싶다. 그래야 서버 설정 변경 없이 상황에 맞게 tool을 조립할 수 있다. | Must |
| US13 | MCP 사용자(LLM)로서, 합성한 음성을 로컬에서 즉시 재생할지 여부를 호출 시점에 결정하고 싶다. 그래야 "재생"이라는 부수효과가 내 의도에 따라서만 일어난다. | Should |
| US14 | MCP 사용자(LLM)로서, 스트리밍이 아닌 일반(one-shot) TTS도 사용할 수 있어야 하고, 호출마다 스트리밍 여부를 선택하고 싶다. 그래야 용도(완결 오디오 vs 점진적 처리)에 맞게 조립할 수 있다. | Must |
| US15 | MCP 사용자(LLM)로서, TTS 모델(`sona_speech_1`/`2`/`2_flash`/`2t`/`3t`, `supertonic_api_1`/`supertonic_api_3` — SDK 0.2.3 기준 7종)을 호출마다 선택하고 싶다. 그래야 품질·속도 trade-off를 상황에 맞게 고를 수 있다. | Must |
| US16 | MCP 사용자(LLM)로서, 특정 custom voice의 상세 정보를 단건 조회하고 싶다. 그래야 검색을 거치지 않고 알고 있는 voice_id의 상태를 바로 확인할 수 있다. | Should |
| US17 | MCP 사용자(LLM)로서, 사용량 내역과 voice별 사용량을 조회하고 싶다. 그래야 크레딧 소비를 분석하고 비용을 관리할 수 있다. | Should |

---

## 6. Functional Requirements

### FR1: `text_to_speech` Tool

수퍼톤 TTS API(`POST /v1/text-to-speech/{voice_id}`)를 호출하여 텍스트를 음성 파일로 변환한다.

**입력 파라미터:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `text` | string | Yes | 변환할 텍스트 (최대 300자) |
| `voice_id` | string | No | 보이스 ID (미지정 시 기본 보이스 사용) |
| `language` | string | No | `ko`, `en`, `ja` 중 택 1 (기본값: `ko`) |
| `output_format` | string | No | `wav` 또는 `mp3` (기본값: `mp3`) |
| `speed` | number | No | 0.5~2.0 (기본값: 1.0) |
| `pitch_shift` | number | No | -12~+12 반음 (기본값: 0) |
| `style` | string | No | 감정 스타일 (예: `neutral`, `happy`) |
| `model` | string | No | TTS 모델 선택 (기본값: `sona_speech_2_flash`). 지원: `sona_speech_1`, `sona_speech_2`, `sona_speech_2_flash`, `sona_speech_2t`, `sona_speech_3t`, `supertonic_api_1`, `supertonic_api_3` (SDK 0.2.3 enum 기준 7종). **스트리밍은 `sona_speech_1`만 지원.** |
| `streaming` | boolean | No | 스트리밍 합성 여부 (기본값: `false`). `false`=일반 one-shot TTS(`create_speech_async`), `true`=스트리밍 TTS(`stream_speech_async`). **`true`는 `model=sona_speech_1`일 때만 허용.** |
| `output_mode` | string | No | `files` / `resources` / `both` (기본값: `files`). 음성 결과 반환 방식을 **호출마다** 결정한다. v0.3에서 `SUPERTONE_MCP_OUTPUT_MODE` 환경변수를 대체한다. |
| `autoplay` | boolean | No | 합성 완료 후 로컬에서 즉시 재생할지 여부 (기본값: `false`). v0.3에서 `SUPERTONE_MCP_AUTOPLAY` 환경변수를 대체한다. macOS는 `afplay` 사용. |
| `include_phonemes` | boolean | No | 오디오와 함께 음소 타이밍 데이터를 반환할지 여부 (기본값: `false`). SDK 0.2.3 신규 필드. |
| `normalized_text` | string | No | 사전 정규화된 텍스트. **`sona_speech_2`/`sona_speech_2_flash` 모델에서만 사용됨** (다른 모델에서는 무시). SDK 0.2.3 신규 필드. |

> **v0.3 변경(BREAKING)**:
> - 출력 방식과 자동 재생은 더 이상 환경변수로 제어하지 않는다. `SUPERTONE_MCP_OUTPUT_MODE`와 `SUPERTONE_MCP_AUTOPLAY`는 제거되며, 각각 위의 `output_mode`·`autoplay` 파라미터로 대체된다. 기존 환경변수를 설정해도 무시된다(또는 시작 시 경고).
> - **스트리밍 기본값 변경**: v0.2까지 `text_to_speech`는 항상 스트리밍(`stream_speech_async`)으로 합성했다. v0.3부터는 `streaming` 파라미터로 호출마다 선택하며 **기본값은 `false`(일반 one-shot TTS)**다. 스트리밍이 필요하면 `streaming=true`를 명시한다.

**`streaming` 동작:**
- `false` (기본) — `create_speech_async`로 전체 오디오를 한 번에 받아 반환. 결과가 완결적이라 `resources` 모드와 잘 맞고 동작이 단순하다.
- `true` — `stream_speech_async`로 청크를 받아 파일에 기록/메모리 수집. 긴 텍스트에서 점진적 처리가 필요할 때 사용.
- **모델 제약**: 스트리밍은 `sona_speech_1`만 지원한다. `streaming=true`인데 `model`이 `sona_speech_1`이 아니면 SDK 호출 전에 **사전 검증(fail-fast)**으로 거절한다 (아래 에러 처리 참고).
- **기본값 주의**: 기본 모델이 `sona_speech_2_flash`(비스트리밍)이므로, 스트리밍을 쓰려면 `streaming=true`와 함께 `model=sona_speech_1`을 **명시적으로** 지정해야 한다.

**`output_mode` 동작:**
- `files` — 음성을 로컬 디렉토리에 저장하고 파일 경로를 반환 (저장 위치는 `SUPERTONE_OUTPUT_DIR`, 기본 `~/supertone-tts-output/`)
- `resources` — 파일을 쓰지 않고 오디오를 MCP 리소스(base64/inline)로 반환
- `both` — 파일로 저장하면서 동시에 MCP 리소스로도 반환

**`autoplay` 기본값 변경:** 기존 환경변수 기본값은 `true`였으나, 레고 컨셉상 "재생"은 명시적 의도여야 하므로 v0.3 파라미터 기본값은 `false`로 둔다.

**출력:**
- `output_mode`에 따라 파일 경로 및/또는 MCP 오디오 리소스를 반환
- 음성 길이(초)를 함께 반환

**긴 텍스트 처리 (v0.3 변경):**
- SDK 0.2.3은 300자를 초과하는 텍스트를 **자동 분할(auto-chunk)**해 병렬 합성 후 오디오를 이어 붙인다(`_auto_chunk_text_async`).
- 따라서 v0.3에서는 MCP 계층의 300자 **하드 거절을 제거**하고 SDK 자동 분할에 위임한다. (FR-005 갱신: 길이 검증은 빈 문자열 등 기본 검증만 유지)
- 매우 긴 입력은 크레딧/지연이 비례 증가하므로 tool 설명에 안내한다(선택적으로 soft-warn).

**에러 처리:**
- API Key 미설정 시 명확한 안내 메시지
- API 호출 실패 시 HTTP 상태 코드와 에러 메시지 전달
- `output_mode`가 `files`/`resources`/`both` 외의 값이면 검증 오류
- `streaming=true`이고 `model`이 `sona_speech_1`이 아니면 검증 오류 (예: `Streaming is only supported by model "sona_speech_1" (received: "{model}"). Set streaming=false or use sona_speech_1.`)

### FR2 (FR-012): `search_voice` Tool — **REPLACES `list_voices` (BREAKING CHANGE in v0.2)**

수퍼톤 API의 `voices.search_voices_async`를 호출하여 다양한 필터로 보이스를 검색한다. 필터를 모두 생략하면 전체 목록을 반환한다 (구 `list_voices` 동작과 동일).

> **Breaking change**: v0.1의 `list_voices` tool은 v0.2에서 제거된다. deprecated alias 없이 완전 교체.

**입력 파라미터** (모두 optional, 서버 사이드 필터링):

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `name` | string | 이름 부분 일치 |
| `description` | string | 설명 부분 일치 |
| `language` | string | 언어 코드 (예: `ko`, `en`, `ja`) |
| `gender` | string | 성별 (예: `male`, `female`) |
| `age` | string | 연령대 (예: `young_adult`, `child`) |
| `use_case` | string | 단일 use case |
| `style` | string | 감정/스타일 |
| `model` | string | 모델명 (예: `sona_speech_1`) |

**출력 (plain text):**
- 번호 매긴 보이스 리스트 (각 항목: voice_id, name, languages, styles)
- 필터가 하나라도 적용된 경우 첫 줄에 `Filters applied: name=..., language=...` 형태로 표시
- 결과 없음: `No voices found matching the filters.`

### FR-013: `get_voice` Tool

특정 voice_id의 상세 정보를 조회한다 (`voices.get_voice_async`).

**입력 파라미터:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `voice_id` | string | Yes | 조회할 voice_id |

**출력 (plain text):**
- voice_id, name, description, age, gender, use_cases, languages, styles, models, sample count, thumbnail_image_url
- 샘플 URL은 별도로 표시하지 않고 `Use preview_voice to fetch sample URLs.` 안내 한 줄을 출력 (URL surfacing은 FR-015 책임)

**에러:**
- `voice_id` 누락/빈 문자열 → `voice_id must not be empty.`

### FR-014: `get_credit_balance` Tool

남은 크레딧을 조회한다 (`usage.get_credit_balance_async`).

**입력 파라미터:** 없음

**출력 (plain text):**
- `Credit balance: {N} chars remaining.`
- API가 plan/expiry 등 추가 필드를 반환하면 다음 줄에 `Plan: {plan_name}` / `Expires: {date}` 형식으로 덧붙인다.

### FR-015: `preview_voice` Tool

특정 voice의 샘플 오디오 URL을 반환한다. v0.2에서는 **재생하지 않고 URL만 반환** (로컬 autoplay는 v3의 `play_audio_url` tool에서 다룸).

**입력 파라미터:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `voice_id` | string | Yes | 대상 voice_id |
| `language` | string | No | 샘플 필터 (해당 언어의 샘플만) |
| `style` | string | No | 샘플 필터 |
| `model` | string | No | 샘플 필터 |

**출력 (plain text, 한 줄에 하나의 샘플):**
```
1. [language=ko, style=happy, model=sona_speech_1] https://.../sample.wav
2. [language=en, style=neutral, model=sona_speech_1] https://.../sample.wav
```

**에러/엣지케이스:**
- voice에 sample이 하나도 없음 → `This voice has no preview samples.`
- 필터에 매칭되는 sample 없음 → `No matching samples for the given filters.`

### FR-016: `predict_duration` Tool

텍스트를 합성하기 전에 결과 음성의 예상 길이(초)를 계산한다 (`text_to_speech.predict_duration_async`). 실제 합성은 일어나지 않는다.

**입력 파라미터** (text 외 모두 optional, 동일한 검증 규칙 적용):

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `text` | string | Yes | 예측 대상 텍스트 (v0.3: 300자 하드 제한 제거, SDK auto-chunk 위임 — FR-001과 동일 규칙) |
| `voice_id` | string | No | (미지정 시 환경변수 기본 voice) |
| `language` | string | No | `ko` / `en` / `ja` (기본 `ko`) |
| `model` | string | No | 모델명 |
| `output_format` | string | No | `wav` / `mp3` |
| `speed` | number | No | 0.5–2.0 |
| `pitch_shift` | number | No | -12–+12 |
| `style` | string | No | 감정 스타일 |

**출력 (plain text):**
- `Predicted duration: 2.34s (credit usage is proportional to duration).`

**에러:** `text_to_speech`의 입력 검증 규칙(FR-006)을 그대로 따른다. 300자 하드 제한은 v0.3에서 제거됨.

### FR-017: `clone_voice` Tool

오디오 파일 하나로부터 커스텀 보이스를 생성한다 (`custom_voices.create_cloned_voice_async`).

**입력 파라미터:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `name` | string | Yes | 새 보이스 이름 (빈 문자열 불가) |
| `audio_path` | string | Yes | 로컬 오디오 파일 경로 (`~` 확장 지원) |
| `description` | string | No | 메모/설명 |

**제약 (사전 검증, fail-fast):**
- 파일 형식: **WAV 또는 MP3만 허용** (확장자 기준)
- 파일 크기: **≤ 3MB** (SDK 한계)
- 단일 파일만 (멀티샘플 업로드는 v3 deferred)
- 파일이 존재하고 읽을 수 있어야 함

**출력 (plain text):**
- `Custom voice created. voice_id: {id}. Use this voice_id in text_to_speech.`

**에러:**
- 파일 없음: `Audio file not found: {path}.`
- 확장자 불일치: `Unsupported audio format: "{ext}". Supported: wav, mp3.`
- 3MB 초과: `Audio file exceeds the 3MB limit (received: {N} bytes).`
- name 빈 문자열: `Voice name must not be empty.`

### FR-018: `search_custom_voice` Tool

생성한 커스텀 보이스를 검색한다 (`custom_voices.search_custom_voices_async`). 페이징은 SDK 내부 기본값 사용.

**입력 파라미터** (모두 optional):

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `name` | string | 이름 부분 일치 |
| `description` | string | 설명 부분 일치 |

**출력 (plain text):**
- 번호 매긴 custom voice 리스트 (voice_id, name, description, created_at if available)
- 결과 없음: `No custom voices found.`

### FR-019: `edit_custom_voice` / `delete_custom_voice` Tools

#### `edit_custom_voice` (`custom_voices.edit_custom_voice_async`)

**입력 파라미터:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `voice_id` | string | Yes | 수정할 custom voice_id |
| `name` | string | No (둘 중 하나는 필수) | 새 이름 |
| `description` | string | No (둘 중 하나는 필수) | 새 설명 |

**부분 업데이트.** `name`과 `description` 모두 미지정이면 검증 오류.

**출력:** `Custom voice updated. voice_id: {id}.`

#### `delete_custom_voice` (`custom_voices.delete_custom_voice_async`)

**입력 파라미터:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `voice_id` | string | Yes | 삭제할 custom voice_id |

**확인 게이트(confirm gate) 없음** — v0.2 단계에서는 tool 설명에 "irreversible" 경고를 명시하는 것으로 갈음한다.

**출력:** `Custom voice deleted. voice_id: {id}.`

### FR-020: `get_custom_voice` Tool (v0.3, SDK 0.2.3 신규 대응)

단일 custom voice의 상세 정보를 조회한다 (`custom_voices.get_custom_voice_async`). v0.2에서는 deferred였으나 SDK가 해당 메소드를 제공하므로 v0.3에서 노출한다.

**입력 파라미터:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `voice_id` | string | Yes | 조회할 custom voice_id |

**출력 (plain text):** voice_id, name, description, created_at 등 상세 필드.

**에러:** `voice_id` 누락/빈 문자열 → `voice_id must not be empty.`

### FR-021: `get_usage_history` Tool (v0.3, SDK 0.2.3 신규 대응)

사용량 내역을 조회한다 (`usage.get_usage_async`). 페이징은 SDK 기본값 사용.

**입력 파라미터:** (모두 optional — SDK가 지원하는 기간/페이징 파라미터 범위 내)

**출력 (plain text):** 기간별 사용량(문자 수/요청 수 등) 요약 리스트.

### FR-022: `get_voice_usage` Tool (v0.3, SDK 0.2.3 신규 대응)

특정 voice의 사용량을 조회한다 (`usage.get_voice_usage_async`).

**입력 파라미터:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `voice_id` | string | Yes | 조회 대상 voice_id |

**출력 (plain text):** 해당 voice의 사용량 요약.

### FR3 (FR-011 in v0.2): 설정 및 인증

v0.3 원칙: **동작 제어 환경변수는 두지 않는다.** 환경변수는 인증과 "변경되지 않는 기본값"에만 사용한다.

| 환경변수 | 분류 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `SUPERTONE_API_KEY` | 인증 | Yes | — | 수퍼톤 API Key. MCP 클라이언트 설정에서 주입 |
| `SUPERTONE_MCP_VOICE_ID` | 기본값 | No | preset voice | `text_to_speech`/`predict_duration`의 기본 `voice_id` (호출 시 `voice_id`로 override 가능) |
| `SUPERTONE_OUTPUT_DIR` | 기본값 | No | `~/supertone-tts-output/` | `output_mode`가 `files`/`both`일 때 파일 저장 위치 |

**제거된 환경변수 (v0.3 BREAKING):**
- `SUPERTONE_MCP_OUTPUT_MODE` → `text_to_speech`의 `output_mode` 파라미터로 이전
- `SUPERTONE_MCP_AUTOPLAY` → `text_to_speech`의 `autoplay` 파라미터로 이전 (기본값 `true`→`false`)

---

## 7. Non-Functional Requirements

| # | 요구사항 | 기준 |
|---|---------|------|
| NFR1 | **설치 용이성** | `uvx supertone-tts-mcp` 또는 `pip install supertone-tts-mcp` 한 줄로 설치 가능 |
| NFR2 | **MCP 호환성** | MCP Python SDK 기반, Claude Desktop과 Cursor에서 정상 동작 |
| NFR3 | **응답 시간** | 수퍼톤 API 응답 시간에 의존 (MCP 서버 자체 오버헤드 < 100ms) |
| NFR4 | **에러 메시지** | API Key 누락, 잘못된 파라미터 등에 대해 사용자가 이해할 수 있는 메시지 제공 |
| NFR5 | **테스트** | pytest 기반 단위 테스트, API 호출은 mock 처리 |

---

## 8. Technical Notes

### 8.1 기술 스택

| 항목 | 선택 | 근거 |
|------|------|------|
| 언어 | **Python 3.11+** | claude.md 기본 언어, uv 워크플로우 활용 |
| MCP SDK | `mcp` (Python SDK) | 공식 SDK |
| HTTP 클라이언트 | `httpx` | async 지원, 현대적 Python HTTP 라이브러리 |
| 패키지 관리 | `uv` | claude.md 표준 |
| 테스트 | `pytest` + `pytest-asyncio` | claude.md 표준 |
| 배포 | PyPI (`supertone-tts-mcp`) | `uvx` 또는 `pip install`로 설치 |
| 레지스트리 | 공식 MCP Registry + PulseMCP | `mcp-publisher` CLI로 등록 |

### 8.2 수퍼톤 API / SDK 요약

v0.2부터는 직접 HTTP가 아닌 공식 **Supertone Python SDK** (`supertone` 패키지)를 통해 다음 모듈을 사용한다.

> **의존성 핀(v0.3)**: `pyproject.toml`이 `supertone`를 버전 미지정으로 두고 있어, SDK가 모델·파라미터·엔드포인트를 추가하면 검증/매핑이 조용히 어긋난다(실제로 SDK 0.2.3에서 모델 2종이 추가됐으나 `SUPPORTED_MODELS`가 따라가지 못해 거절되고 있었음). 따라서 **버전 범위를 명시**한다: 예) `supertone>=0.2.3,<0.3`. 현재 검증 기준 SDK 버전: **0.2.3**.

| SDK 모듈 | 메소드 | MCP tool |
|----------|--------|----------|
| `text_to_speech` | `create_speech_async` (일반), `stream_speech_async` (스트리밍) | `text_to_speech` (FR-001, `streaming` 파라미터로 선택) |
| `text_to_speech` | `predict_duration_async` | `predict_duration` (FR-016) |
| `voices` | `search_voices_async` | `search_voice` (FR-012) |
| `voices` | `get_voice_async` | `get_voice` (FR-013) |
| `voices` (samples 필드) | — | `preview_voice` (FR-015) |
| `usage` | `get_credit_balance_async` | `get_credit_balance` (FR-014) |
| `usage` | `get_usage_async` | `get_usage_history` (FR-021, v0.3 신규) |
| `usage` | `get_voice_usage_async` | `get_voice_usage` (FR-022, v0.3 신규) |
| `custom_voices` | `create_cloned_voice_async` | `clone_voice` (FR-017) |
| `custom_voices` | `search_custom_voices_async` | `search_custom_voice` (FR-018) |
| `custom_voices` | `get_custom_voice_async` | `get_custom_voice` (FR-020, v0.3 신규) |
| `custom_voices` | `edit_custom_voice_async` | `edit_custom_voice` (FR-019) |
| `custom_voices` | `delete_custom_voice_async` | `delete_custom_voice` (FR-019) |

- **Base URL / 인증**: SDK가 환경변수 `SUPERTONE_API_KEY`로 자동 처리
- **응답**: TTS는 audio bytes (또는 stream), 그 외는 typed response 객체
- **제한**: 텍스트 최대 300자, 요금제별 rate limit (20-60 req/min), clone audio ≤3MB

### 8.3 MCP 서버 구조

```
supertone-tts-mcp/
├── pyproject.toml
├── src/
│   └── supertone_tts_mcp/
│       ├── __init__.py
│       ├── server.py          # MCP 서버 진입점
│       ├── tools.py           # text_to_speech, search_voice, get_voice, get_credit_balance,
│       │                      # preview_voice, predict_duration, clone_voice,
│       │                      # search/edit/delete_custom_voice 구현
│       └── supertone_client.py # 수퍼톤 API 래핑
├── tests/
│   ├── test_tools.py
│   └── test_supertone_client.py
├── server.json             # MCP Registry 등록용 메타데이터
└── README.md
```

### 8.4 MCP 클라이언트 설정 예시 (Claude Desktop)

```json
{
  "mcpServers": {
    "supertone-tts": {
      "command": "uvx",
      "args": ["supertone-tts-mcp"],
      "env": {
        "SUPERTONE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### 8.5 MCP Registry 배포

PyPI 배포 후 공식 MCP Registry에 등록하여 검색/설치 가능하게 한다.

**등록 절차:**
```bash
# 1. CLI 설치
brew install mcp-publisher

# 2. 설정 파일 생성 (server.json)
mcp-publisher init

# 3. GitHub 인증
mcp-publisher login github

# 4. 등록
mcp-publisher publish
```

**server.json 예시:**
```json
{
  "$schema": "https://static.modelcontextprotocol.io/schemas/2025-07-09/server.schema.json",
  "name": "io.github.pillip/supertone-tts",
  "description": "High-quality TTS powered by Supertone API — Korean voice synthesis with emotion control, voice search & preview, duration prediction, and voice cloning",
  "version": "0.2.0",
  "packages": [
    {
      "registry_type": "pypi",
      "identifier": "supertone-tts-mcp",
      "version": "0.2.0"
    }
  ]
}
```

**추가 등록 대상:**
- [공식 MCP Registry](https://registry.modelcontextprotocol.io/) — `mcp-publisher`로 등록
- [PulseMCP](https://pulsemcp.com/) — 셀프 등록 (5,500+ 서버 등록된 커뮤니티 디렉토리)
- [GitHub MCP Registry](https://github.blog/ai-and-ml/github-copilot/meet-the-github-mcp-registry-the-fastest-way-to-discover-mcp-servers/) — GitHub 릴리스 기반

PyPI README에 아래 메타데이터 포함 필수:
```
mcp-name: io.github.pillip/supertone-tts
```

### 8.6 음성 결과 전달 방식 (v0.3: per-call `output_mode`)

v0.2까지는 환경변수 `SUPERTONE_MCP_OUTPUT_MODE`로 서버 전역 고정이었으나, v0.3부터는 `text_to_speech` 호출 파라미터 `output_mode`로 매 호출 결정한다.

- `files` (기본) — 오디오를 로컬 파일로 저장하고 경로를 반환 (예: `~/supertone-tts-output/2026-06-05_abc123.mp3`). 저장 위치는 `SUPERTONE_OUTPUT_DIR`.
- `resources` — 파일을 쓰지 않고 오디오를 MCP 리소스(base64/inline)로 반환. 클라이언트가 파일시스템 접근 없이 바로 사용 가능.
- `both` — 위 둘을 동시에 반환.

`autoplay=true`인 경우 합성 완료 후 OS 기본 재생기(macOS `afplay`)로 로컬 재생한다. 이는 명시적 부수효과이며 기본값은 `false`.

---

## 9. Success Metrics

| # | 지표 | 목표 (출시 후 3개월) |
|---|------|-------------------|
| SM1 | GitHub stars | 50+ |
| SM2 | PyPI 다운로드 수 | 200+ |
| SM3 | 공식 MCP Registry 등록 | 등록 완료 + 검색 가능 확인 |
| SM4 | Claude Desktop + Cursor에서 정상 동작 | 2개 클라이언트 모두 확인 |
| SM5 | MCP 학습 목표 달성 | MCP 서버 개발 프로세스 숙달 (주관적) |

---

## 10. Milestones

### v0.1 (released)
| 단계 | 내용 | 예상 기간 |
|------|------|----------|
| M1 | 수퍼톤 API 연동 확인 (단독 스크립트) | 1일 |
| M2 | MCP 서버 구현 (`text_to_speech` + `list_voices`) | 2-3일 |
| M3 | 테스트 작성 + Claude Desktop에서 동작 확인 | 1-2일 |

### v0.2 (current)
| 단계 | 내용 | 예상 기간 |
|------|------|----------|
| M4 | v0.2 구현: voice discovery (`search_voice`, `get_voice`, `get_credit_balance`, `preview_voice`), `predict_duration`, voice cloning CRUD (`clone_voice`, `search/edit/delete_custom_voice`). `list_voices` → `search_voice` 교체 (breaking) | 3-5일 |
| M5 | README/문서 갱신 + PyPI 0.2.0 배포 + MCP Registry 메타데이터 업데이트 | 1일 |

**v0.2 총 예상 기간**: 1주

### v0.3 (concept pivot — current)
| 단계 | 내용 | 예상 기간 |
|------|------|----------|
| M6 | 동작 제어 환경변수 제거: `SUPERTONE_MCP_OUTPUT_MODE`·`SUPERTONE_MCP_AUTOPLAY` → `output_mode`·`autoplay` 파라미터로 이전 (breaking). `streaming` 파라미터 추가(기본 `false`, 일반 TTS `create_speech_async` 경로 연결, 기존 stream 경로는 `true`). **`streaming=true` × non-`sona_speech_1` 조합 사전 검증(fail-fast) 추가.** `model` 파라미터 PRD/문서 명시(코드엔 이미 존재). **`SUPPORTED_MODELS`를 SDK 0.2.3 enum과 동기화 (`sona_speech_3t`·`supertonic_api_3` 추가 — `_MODEL_MAP`은 enum 기반이라 이미 수용하나 `validate_model`이 거절 중), `DEFAULT_MODEL`을 `sona_speech_1`→`sona_speech_2_flash`로 변경.** 관련 resolve 헬퍼/검증/테스트 갱신 | 1-2일 |
| M7 | SDK 0.2.3 대응: 300자 하드 제한 제거(SDK auto-chunk 위임), `include_phonemes`·`normalized_text` 파라미터 노출, 신규 tool 추가(`get_custom_voice`, `get_usage_history`, `get_voice_usage`), `pyproject.toml` SDK 버전 핀(`supertone>=0.2.3,<0.3`) | 2-3일 |
| M8 | 컨셉 문서화: PRD/README "composable SDK toolkit" 프레이밍 반영, 환경변수 표 갱신, 마이그레이션 안내(구 env var → 신 param) | 1일 |
| M9 | PyPI 0.3.0 배포 + MCP Registry 메타데이터/설명 업데이트 | 1일 |

**v0.3 총 예상 기간**: 5-7일

---

## 11. Future Considerations (v0.4+)

- **로컬 오디오 자동 재생** (`play_audio_url`) — `preview_voice`가 반환한 URL을 OS 기본 플레이어로 재생
- **멀티샘플 voice clone** — 여러 오디오 파일을 한 번에 업로드하여 보다 안정적인 커스텀 보이스 생성
- **`list_models`** tool — 사용 가능한 TTS 모델 목록 조회
- **delete confirm gate** — `delete_custom_voice`에 명시적 확인 단계 추가
- **배치 변환** (`batch_tts`) — 여러 문장을 한 번에 변환
- **스트리밍 TTS 개선** — 이미 v0.1.x에서 streaming wrapper를 도입함; 향후 chunked progress notification 추가
- **STT(Speech-to-Text)** — MCP 구조와 맞지 않아 별도 프로젝트로 분리
