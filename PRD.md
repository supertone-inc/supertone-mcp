# PRD: Supertone TTS MCP Server

> Status: Draft
> Version: v0.2 (voice discovery + cloning)
> Date: 2026-05-26
> Author: pillip

---

## 1. Background

MCP(Model Context Protocol)는 LLM 클라이언트(Claude Desktop, Cursor, OpenClaw 등)에서 외부 도구를 연동하는 표준 프로토콜로, 2024년 11월 출시 이후 폭발적으로 성장 중이다(10,000+ 서버, 5개월간 다운로드 80배 증가).

수퍼톤(Supertone)은 HYBE 자회사로 한국어 특화 고품질 TTS를 제공하며, API를 통해 23개 언어의 음성 합성을 지원한다. 현재 MCP 생태계에 TTS 서버는 5개 이상 존재하나, **수퍼톤 기반 MCP 서버는 없다.**

이 프로젝트는 수퍼톤 TTS API를 MCP 서버로 래핑하여 배포함으로써:
1. MCP 서버 개발 기술을 습득하고
2. 수퍼톤 API 사용량을 간접적으로 증가시키는 것을 목표로 한다.

---

## 2. Goals

| # | 목표 | 측정 기준 |
|---|------|----------|
| G1 | MCP 서버 개발 역량 확보 | MCP 표준을 준수하는 동작하는 서버 완성 |
| G2 | 수퍼톤 TTS를 MCP 생태계에 진입시킴 | Claude Desktop + Cursor에서 정상 동작 확인 |
| G3 | 오픈소스로 배포하여 외부 사용자 확보 | GitHub 공개 + PyPI 배포 |

---

## 3. Non-Goals (Out of Scope)

- STT(Speech-to-Text) 기능 — MCP의 구조(LLM이 tool 호출)와 맞지 않음
- 음성 대화 인터페이스 (STT→LLM→TTS) — 별도 프로젝트로 분리
- 배치 변환(batch TTS) — v3에서 고려
- 다중 파일 voice clone (멀티샘플 업로드) — v3에서 고려 (v0.2는 단일 파일만)
- 로컬 자동 재생(autoplay) for preview_voice — v3의 `play_audio_url` tool에서 다룸 (v0.2는 URL 반환만)
- 모델 목록 조회 (`list_models`) — v3에서 고려 (현재는 SDK 기본값 사용)
- 단일 custom voice 조회 (`get_custom_voice`) — `search_custom_voice` 결과로 충분하므로 v3에서 재평가
- 삭제 확인 게이트 (delete confirm prompt) — v0.2는 tool 설명 경고만으로 충분
- 웹 UI 또는 별도 클라이언트 앱
- 수퍼톤 외 다른 TTS 엔진 지원

---

## 4. Target Users

### Primary: MCP 사용자 (개발자/크리에이터)
- Claude Desktop, Cursor, OpenClaw 등 MCP 지원 클라이언트를 사용하는 사람
- LLM과 대화하면서 텍스트를 음성으로 변환하고 싶은 경우
- 예: "이 문장을 한국어 음성으로 만들어줘", "오늘 뉴스를 요약해서 음성 브리핑으로 만들어줘"

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

**출력:**
- 생성된 음성 파일을 로컬 디렉토리에 저장
- 파일 경로와 음성 길이(초)를 반환
- 저장 디렉토리는 환경변수(`SUPERTONE_OUTPUT_DIR`)로 설정 가능, 기본값은 `~/supertone-tts-output/`

**에러 처리:**
- API Key 미설정 시 명확한 안내 메시지
- 300자 초과 시 텍스트 자동 분할 없이 에러 반환 (사용자가 직접 분할)
- API 호출 실패 시 HTTP 상태 코드와 에러 메시지 전달

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
| `text` | string | Yes | 예측 대상 텍스트 (최대 300자, FR-005 동일) |
| `voice_id` | string | No | (미지정 시 환경변수 기본 voice) |
| `language` | string | No | `ko` / `en` / `ja` (기본 `ko`) |
| `model` | string | No | 모델명 |
| `output_format` | string | No | `wav` / `mp3` |
| `speed` | number | No | 0.5–2.0 |
| `pitch_shift` | number | No | -12–+12 |
| `style` | string | No | 감정 스타일 |

**출력 (plain text):**
- `Predicted duration: 2.34s (credit usage is proportional to duration).`

**에러:** `text_to_speech`의 입력 검증 규칙(FR-005, FR-006)을 그대로 따른다.

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

### FR3 (FR-011 in v0.2): 설정 및 인증

- 수퍼톤 API Key는 환경변수 `SUPERTONE_API_KEY`로 제공
- MCP 클라이언트의 서버 설정에서 환경변수로 주입하는 표준 방식 사용

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

| SDK 모듈 | 메소드 | MCP tool |
|----------|--------|----------|
| `text_to_speech` | `text_to_speech_async` | `text_to_speech` (FR-001) |
| `text_to_speech` | `predict_duration_async` | `predict_duration` (FR-016) |
| `voices` | `search_voices_async` | `search_voice` (FR-012) |
| `voices` | `get_voice_async` | `get_voice` (FR-013) |
| `voices` (samples 필드) | — | `preview_voice` (FR-015) |
| `usage` | `get_credit_balance_async` | `get_credit_balance` (FR-014) |
| `custom_voices` | `create_cloned_voice_async` | `clone_voice` (FR-017) |
| `custom_voices` | `search_custom_voices_async` | `search_custom_voice` (FR-018) |
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

### 8.6 음성 파일 전달 방식

MCP에서 바이너리 파일 전달은 제한적이므로:
1. 수퍼톤 API에서 받은 오디오 스트림을 **로컬 파일로 저장**
2. **파일 경로**를 텍스트로 반환 (예: `~/supertone-tts-output/2026-03-13_abc123.mp3`)
3. 사용자가 해당 경로의 파일을 재생

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

---

## 11. Future Considerations (v0.3+)

- **로컬 오디오 자동 재생** (`play_audio_url`) — `preview_voice`가 반환한 URL을 OS 기본 플레이어로 재생
- **멀티샘플 voice clone** — 여러 오디오 파일을 한 번에 업로드하여 보다 안정적인 커스텀 보이스 생성
- **`list_models`** tool — 사용 가능한 TTS 모델 목록 조회
- **`get_custom_voice`** (단일 조회) — 현재는 `search_custom_voice` 결과로 갈음
- **delete confirm gate** — `delete_custom_voice`에 명시적 확인 단계 추가
- **배치 변환** (`batch_tts`) — 여러 문장을 한 번에 변환
- **스트리밍 TTS 개선** — 이미 v0.1.x에서 streaming wrapper를 도입함; 향후 chunked progress notification 추가
- **300자 초과 텍스트 자동 분할 및 연결**
- **STT(Speech-to-Text)** — MCP 구조와 맞지 않아 별도 프로젝트로 분리
