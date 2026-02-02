# DeVine AI Server 구현 문서

## 개요

DeVine AI Server는 프로젝트 리포트 JSON을 받아 임베딩 벡터를 생성하는 FastAPI 기반 서버입니다.
생성된 벡터는 Spring 서버에서 pgvector를 통해 유사도 검색에 활용됩니다.

## 아키텍처

```
[Spring Server] → POST /embed → [DeVine AI Server] → [OpenAI API]
                                        ↓
                                   임베딩 벡터 반환
                                        ↓
[Spring Server] ← 벡터 저장 (pgvector) ← 유사도 검색
```

## 프로젝트 구조

```
DeVine_AI/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 앱, 엔드포인트, 예외 핸들러
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # 환경 변수 설정
│   │   ├── exceptions.py       # 커스텀 예외 및 에러 코드
│   │   └── response.py         # 응답 모델
│   ├── services/
│   │   ├── __init__.py
│   │   └── embedding_service.py # OpenAI 임베딩 서비스
│   └── utils/
│       ├── __init__.py
│       └── text_processor.py   # 텍스트 추출 유틸리티
├── tests/
│   ├── __init__.py
│   └── test_core.py            # 테스트 스크립트
├── .env                        # 환경 변수 (gitignore)
├── .env.example                # 환경 변수 예시
├── requirements.txt            # 의존성
└── test.html                   # 브라우저 테스트 UI
```

## 환경 설정

### 환경 변수 (.env)

```env
OPENAI_API_KEY=sk-...           # 필수: OpenAI API 키
EMBEDDING_MODEL=text-embedding-3-small  # 임베딩 모델 (기본값)
LOG_LEVEL=INFO                  # 로그 레벨: DEBUG, INFO, WARNING, ERROR
DEBUG=false                     # true: 에러 상세 정보 노출
```

### 의존성 설치

```bash
pip install -r requirements.txt
```

### 서버 실행

```bash
uvicorn app.main:app --reload
```

## API 명세

### 헬스 체크

```
GET /health
```

**응답:**
```json
{
  "status": "healthy",
  "service": "DeVine AI Server"
}
```

### 임베딩 생성

```
POST /embed
Content-Type: application/json
```

**요청:**
```json
{
  "report": {
    "overview": {
      "summary": "프로젝트 요약...",
      "mainTech": "주요 기술..."
    },
    "projectInfo": {
      "techStack": ["JavaScript", "Express.js", "Prisma"]
    },
    "keyImplementations": [
      { "title": "구현 기능 1" },
      { "title": "구현 기능 2" }
    ]
  }
}
```

**성공 응답 (200):**
```json
{
  "vector": [0.123, -0.456, ...],
  "dimension": 1536
}
```

**에러 응답 (4xx, 5xx):**
```json
{
  "success": false,
  "error_code": "EMPTY_TEXT",
  "message": "리포트에서 임베딩할 텍스트를 추출할 수 없습니다.",
  "detail": null
}
```

## 핵심 구현 상세

### 1. 텍스트 추출 (`text_processor.py`)

#### 1.1 왜 텍스트 추출이 필요한가?

임베딩 모델은 텍스트를 입력으로 받습니다. 리포트 JSON을 그대로 임베딩하면:
- JSON 구조 문자(`{`, `}`, `"`, `:`)가 노이즈로 작용
- 불필요한 필드(scale, capabilities 등)가 벡터에 영향
- 검색 정확도 저하

따라서 **프로젝트의 핵심 특성을 나타내는 필드만** 추출하여 자연어 텍스트로 변환합니다.

#### 1.2 전체 필드 포함/제외 매핑

리포트 JSON의 **모든 필드**에 대한 포함/제외 여부입니다.

| 필드 경로 | 포함 | 제외 이유 |
|----------|:----:|----------|
| **overview** | | |
| `overview.summary` | ✅ | - |
| `overview.mainTech` | ✅ | - |
| `overview.capabilities` | ❌ | summary와 중복되는 내용 |
| `overview.scale` | ❌ | 숫자 정보로 유사도 검색에 불필요 |
| **projectInfo** | | |
| `projectInfo.projectName` | ❌ | 프로젝트 이름만으로는 특성 파악 어려움 |
| `projectInfo.techStack` | ✅ | - |
| `projectInfo.scale` | ❌ | 숫자 정보로 유사도 검색에 불필요 |
| **keyImplementations** | | |
| `keyImplementations[].title` | ✅ | **배열 내 모든 title 추출 (개수 제한 없음)** |
| `keyImplementations[].description` | ❌ | title에 핵심 내용이 요약되어 있음 |
| `keyImplementations[].capabilities` | ❌ | 상세 기술 목록으로 노이즈 가능성 |
| **aiEvaluation** | | |
| `aiEvaluation[].title` | ❌ | AI 평가 내용으로 프로젝트 특성과 무관 |
| `aiEvaluation[].details` | ❌ | AI 평가 내용으로 프로젝트 특성과 무관 |
| **recommendations** | | |
| `recommendations[]` | ❌ | 추천 직무로 프로젝트 자체 설명이 아님 |

#### 1.3 포함 필드 선정 이유

| 필드 | 선정 이유 |
|------|----------|
| `overview.summary` | 프로젝트 전체를 설명하는 핵심 문장 |
| `overview.mainTech` | 사용한 주요 기술/프레임워크 |
| `projectInfo.techStack` | 기술 스택 키워드 (검색에 중요) |
| `keyImplementations[].title` | 구현한 기능들의 핵심 키워드 |

#### 1.4 keyImplementations 처리 방식

`keyImplementations`는 **배열**이며, 배열 내 **모든 항목의 title**을 추출합니다.

```
keyImplementations 배열 (N개)          추출 결과
────────────────────────────────────────────────────────
[
  {title: "A", description: "..."},  → "A" 추출
  {title: "B", description: "..."},  → "B" 추출
  {title: "C", description: "..."},  → "C" 추출
  ... (N개)                          → N개 전부 추출
]
```

**예시 - 백엔드 리포트 (3개):**
```
외부 음악 서비스 API 통합 및 데이터 관리
사용자 인증 및 권한 부여 시스템
AI 기반 음악 추천 및 사용자 맞춤형 서비스
```

**예시 - 프론트엔드 리포트 (5개):**
```
사용자 인증 및 권한 관리
다양한 콘텐츠(아카이브, 다이어리, 티켓) 관리 시스템
커뮤니티 기능 구현 (게시글, 댓글, 좋아요)
클라우드 기반 파일 멀티파트 업로드
컴포넌트 기반 UI/UX 및 테마 시스템
```

#### 1.5 변환 과정 상세

```
입력 JSON                              추출 및 변환                    출력 텍스트
─────────────────────────────────────────────────────────────────────────────────

{
  "overview": {
    "summary": "이 프로젝트는...",  ──→ parts.append(summary)     ──→ "이 프로젝트는..."
    "mainTech": "JavaScript 기반...", → parts.append(mainTech)    ──→ "JavaScript 기반..."
    "capabilities": [...],             (제외)
    "scale": "8,625줄"                 (제외)
  },
  "projectInfo": {
    "projectName": "UMC Archive",      (제외)
    "techStack": [                 ──→ ", ".join(techStack)      ──→ "JavaScript, Express.js, ..."
      "JavaScript",
      "Express.js",
      ...
    ]
  },
  "keyImplementations": [
    {"title": "외부 음악 서비스..."}, ─→ parts.append(title)       ──→ "외부 음악 서비스..."
    {"title": "사용자 인증..."},     ─→ parts.append(title)       ──→ "사용자 인증..."
    ...
  ]
}
                                       "\n".join(parts)
                                            │
                                            ▼
                                       최종 텍스트 출력
```

#### 1.6 코드 동작 설명

```python
def extract_embedding_text(report: dict[str, Any]) -> str:
    parts: list[str] = []  # 추출된 텍스트 조각들을 저장할 리스트

    # 1단계: overview.summary 추출
    overview = report.get("overview", {})  # overview가 없으면 빈 딕셔너리
    if summary := overview.get("summary"): # 왈러스 연산자: 값이 있으면 할당하고 True
        parts.append(summary)

    # 2단계: overview.mainTech 추출
    if main_tech := overview.get("mainTech"):
        parts.append(main_tech)

    # 3단계: projectInfo.techStack 추출 (리스트 → 문자열 변환)
    project_info = report.get("projectInfo", {})
    if tech_stack := project_info.get("techStack"):
        if isinstance(tech_stack, list):  # 타입 검증
            parts.append(", ".join(tech_stack))  # ["A", "B"] → "A, B"

    # 4단계: keyImplementations[].title 추출 (배열 순회)
    key_implementations = report.get("keyImplementations", [])
    for impl in key_implementations:
        if title := impl.get("title"):
            parts.append(title)

    # 5단계: 줄바꿈으로 연결하여 최종 텍스트 생성
    return "\n".join(parts)
```

#### 1.7 실제 변환 예시

**입력 JSON:**
```json
{
  "overview": {
    "summary": "이 프로젝트는 다양한 외부 음악 API(Last.fm, iTunes, Spotify)와 연동하여 음악 정보를 제공하는 백엔드 시스템입니다.",
    "mainTech": "JavaScript 기반 Express.js 프레임워크를 활용한 백엔드 API 서버 개발",
    "capabilities": ["JWT 인증", "외부 API 연동"],
    "scale": "약 8,625줄"
  },
  "projectInfo": {
    "projectName": "UMC Archive Backend",
    "techStack": ["JavaScript", "Express.js", "Prisma", "OpenAI API", "AWS SDK (S3)"]
  },
  "keyImplementations": [
    {
      "title": "외부 음악 서비스 API 통합 및 데이터 관리",
      "description": "Last.fm, iTunes, Spotify..."
    },
    {
      "title": "사용자 인증 및 권한 부여 시스템",
      "description": "JWT를 이용한..."
    },
    {
      "title": "AI 기반 음악 추천 및 사용자 맞춤형 서비스",
      "description": "OpenAI GPT API를 활용..."
    }
  ]
}
```

**출력 텍스트:**
```
이 프로젝트는 다양한 외부 음악 API(Last.fm, iTunes, Spotify)와 연동하여 음악 정보를 제공하는 백엔드 시스템입니다.
JavaScript 기반 Express.js 프레임워크를 활용한 백엔드 API 서버 개발
JavaScript, Express.js, Prisma, OpenAI API, AWS SDK (S3)
외부 음악 서비스 API 통합 및 데이터 관리
사용자 인증 및 권한 부여 시스템
AI 기반 음악 추천 및 사용자 맞춤형 서비스
```

**총 6줄, 각 줄의 역할:**
| 줄 | 내용 | 역할 |
|----|------|------|
| 1 | summary | 프로젝트가 무엇인지 설명 |
| 2 | mainTech | 어떤 기술로 만들었는지 |
| 3 | techStack | 사용한 기술 키워드들 |
| 4-6 | implementation titles | 구현한 주요 기능들 |

---

### 2. 임베딩 서비스 (`embedding_service.py`)

#### 2.1 임베딩이란?

임베딩은 텍스트를 **고정 길이의 숫자 벡터**로 변환하는 과정입니다.

```
텍스트: "JavaScript 백엔드 개발"
                │
                ▼ (OpenAI Embedding API)
                │
벡터: [0.023, -0.041, 0.067, ..., 0.012]  (1536개의 숫자)
```

**왜 벡터로 변환하는가?**
- 텍스트는 직접 비교가 어려움 ("백엔드 개발" vs "서버 개발" → 다른 문자열)
- 벡터는 수학적 연산 가능 (코사인 유사도로 의미적 유사성 측정)
- 유사한 의미의 텍스트는 벡터 공간에서 가까운 위치에 존재

#### 2.2 사용 모델: text-embedding-3-small

| 항목 | 값 |
|------|-----|
| 모델명 | `text-embedding-3-small` |
| 출력 차원 | 1536 |
| 최대 입력 토큰 | 8191 |
| 비용 | $0.00002 / 1K 토큰 |

**왜 이 모델을 선택했는가?**
- `text-embedding-3-large` (3072차원) 대비 저렴하고 빠름
- 프로젝트 유사도 검색에는 1536차원으로 충분
- OpenAI의 최신 임베딩 모델 (2024년 출시)

#### 2.3 임베딩 과정 상세

```
┌─────────────────────────────────────────────────────────────────┐
│                    EmbeddingService.create_embedding()          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. 입력 텍스트 수신                                              │
│    text = "이 프로젝트는... JavaScript... 외부 음악 서비스..."    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. OpenAI API 호출                                              │
│    POST https://api.openai.com/v1/embeddings                    │
│    {                                                            │
│      "model": "text-embedding-3-small",                         │
│      "input": "이 프로젝트는... JavaScript..."                   │
│    }                                                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
            [성공 응답]               [에러 발생]
                    │                       │
                    ▼                       ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│ 3a. 벡터 추출            │    │ 3b. 재시도 로직 실행      │
│ response.data[0].embedding│    │ RateLimitError →재시도   │
│ → [0.023, -0.041, ...]   │    │ APIConnectionError→재시도 │
└──────────────────────────┘    │ 그 외 에러 → 즉시 실패   │
            │                   └──────────────────────────┘
            ▼                               │
┌──────────────────────────┐               │
│ 4. 벡터 반환             │◀──────────────┘
│ list[float] (1536개)     │   (최대 3회 재시도 후 성공 시)
└──────────────────────────┘
```

#### 2.4 코드 동작 설명

```python
class EmbeddingService:
    def __init__(self):
        settings = get_settings()
        # AsyncOpenAI: 비동기 HTTP 클라이언트 (동시 요청 처리에 유리)
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EMBEDDING_MODEL  # "text-embedding-3-small"

    @retry(
        # 재시도할 예외 타입 지정
        retry=retry_if_exception_type((RateLimitError, APIConnectionError)),
        # 최대 3번 시도 (1번 실패 + 2번 재시도)
        stop=stop_after_attempt(3),
        # 지수 백오프: 2초 → 4초 → 8초 (최대 10초)
        wait=wait_exponential(multiplier=1, min=2, max=10),
        # 재시도 전 로그 출력
        before_sleep=lambda retry_state: logger.warning(
            f"Retry attempt {retry_state.attempt_number} after error"
        ),
    )
    async def create_embedding(self, text: str) -> list[float]:
        try:
            # OpenAI API 호출
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
            )
            # 응답에서 벡터 추출
            # response.data = [EmbeddingObject(embedding=[...], index=0)]
            return response.data[0].embedding

        except (RateLimitError, APIConnectionError):
            # 재시도 가능한 에러: tenacity가 자동 재시도
            raise
        except APIError as e:
            # 재시도 불가능한 에러: 즉시 실패
            logger.error(f"OpenAI API error: {e}")
            raise
```

#### 2.5 재시도 로직 상세

**재시도 대상 에러:**
| 에러 타입 | 발생 상황 | 재시도 이유 |
|----------|----------|------------|
| `RateLimitError` | API 호출 한도 초과 | 잠시 후 재시도하면 성공 가능 |
| `APIConnectionError` | 네트워크 일시적 장애 | 재연결 시 성공 가능 |

**재시도하지 않는 에러:**
| 에러 타입 | 발생 상황 | 재시도 안 하는 이유 |
|----------|----------|-------------------|
| `AuthenticationError` | API 키 오류 | 재시도해도 동일한 결과 |
| `BadRequestError` | 잘못된 요청 | 요청 자체가 잘못됨 |

**지수 백오프 (Exponential Backoff):**
```
1차 시도: 실패
    ↓ 2초 대기
2차 시도: 실패
    ↓ 4초 대기 (2 × 2)
3차 시도: 실패
    ↓ 예외 발생 (최대 시도 횟수 초과)
```

#### 2.6 API 응답 구조

**OpenAI Embedding API 응답:**
```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "index": 0,
      "embedding": [
        0.0234375,
        -0.041015625,
        0.0673828125,
        ... (총 1536개)
      ]
    }
  ],
  "model": "text-embedding-3-small",
  "usage": {
    "prompt_tokens": 42,
    "total_tokens": 42
  }
}
```

**벡터 추출:**
```python
response.data[0].embedding  # [0.0234375, -0.041015625, ...]
```

#### 2.7 벡터의 의미

생성된 1536차원 벡터의 각 숫자는 텍스트의 의미적 특성을 나타냅니다.

```
벡터: [0.023, -0.041, 0.067, 0.089, -0.012, ...]
       │       │       │       │       │
       │       │       │       │       └─ 1536번째 특성
       │       │       │       └─ 4번째 특성
       │       │       └─ 3번째 특성
       │       └─ 2번째 특성
       └─ 1번째 특성
```

**유사도 계산 (코사인 유사도):**
```
프로젝트 A 벡터: [0.1, 0.2, 0.3, ...]
프로젝트 B 벡터: [0.1, 0.2, 0.3, ...]  → 유사도 ≈ 1.0 (매우 유사)
프로젝트 C 벡터: [-0.3, 0.5, -0.1, ...] → 유사도 ≈ 0.2 (다름)
```

이 벡터를 pgvector에 저장하고, 검색 시 코사인 유사도로 비교하여 유사한 프로젝트를 찾습니다.

### 3. 예외 처리 (`exceptions.py`)

Spring의 `@ControllerAdvice`와 유사한 전역 예외 처리 구조입니다.

**에러 코드:**
| 코드 | HTTP 상태 | 설명 |
|------|----------|------|
| `EMPTY_TEXT` | 400 | 임베딩할 텍스트 없음 |
| `INVALID_REPORT_FORMAT` | 400 | 리포트 형식 오류 |
| `OPENAI_API_ERROR` | 500 | OpenAI API 호출 실패 |
| `EMBEDDING_FAILED` | 500 | 임베딩 생성 실패 |
| `INTERNAL_ERROR` | 500 | 예상치 못한 서버 오류 |

**예외 클래스 계층:**
```
Exception
└── AppException (기본 예외)
    ├── BadRequestException (400)
    └── InternalServerException (500)
```

### 4. 의존성 주입

FastAPI의 `Depends`를 활용한 의존성 주입 패턴입니다.

```python
# 서비스를 app.state에 저장
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.embedding_service = EmbeddingService()
    yield

# 의존성 함수
def get_embedding_service(request: Request) -> EmbeddingService:
    return request.app.state.embedding_service

# 엔드포인트에서 주입받아 사용
@app.post("/embed")
async def embed_report(
    request: EmbeddingRequest,
    embedding_service: EmbeddingService = Depends(get_embedding_service),
):
    ...
```

### 5. 로깅

환경 변수로 로그 레벨을 제어합니다.

**로그 레벨별 출력:**
| 레벨 | 출력 내용 |
|------|----------|
| DEBUG | 리포트 키, 추출된 텍스트 길이 |
| INFO | 요청 수신, 임베딩 완료, 서버 시작/종료 |
| WARNING | API 재시도 |
| ERROR | 임베딩 실패, 예외 발생 |

**로그 포맷:**
```
2024-01-15 10:30:00 - app.main - INFO - 임베딩 요청 수신
2024-01-15 10:30:01 - app.main - INFO - 임베딩 생성 완료 (dimension: 1536)
```

### 6. 보안

**DEBUG 모드에 따른 에러 응답:**

| 환경 | DEBUG | detail 필드 |
|------|-------|------------|
| 개발 | `true` | 실제 에러 메시지 노출 |
| 프로덕션 | `false` | `null` (숨김) |

```python
# 프로덕션 응답 예시
{
  "success": false,
  "error_code": "OPENAI_API_ERROR",
  "message": "OpenAI API 호출 중 오류가 발생했습니다.",
  "detail": null  # 실제 에러 내용 숨김
}
```

## 테스트

### 브라우저 테스트

1. 서버 실행: `uvicorn app.main:app --reload`
2. `test.html` 파일을 브라우저에서 열기
3. 샘플 데이터 로드 후 "임베딩 생성" 클릭

### CLI 테스트

```bash
python -m tests.test_core
```

### cURL 테스트

```bash
# 헬스 체크
curl http://localhost:8000/health

# 임베딩 생성
curl -X POST http://localhost:8000/embed \
  -H "Content-Type: application/json" \
  -d '{"report": {"overview": {"summary": "테스트 프로젝트"}}}'
```

## Spring 연동 시 참고사항

### CORS 설정

Spring에서 호출 시 CORS 설정이 필요하면 `main.py`에 추가:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Spring 서버 주소
    allow_methods=["POST"],
    allow_headers=["*"],
)
```

### 벡터 저장 (pgvector)

Spring에서 받은 벡터를 pgvector에 저장하는 예시:

```sql
-- 테이블 생성
CREATE TABLE report_embeddings (
    id SERIAL PRIMARY KEY,
    report_id BIGINT NOT NULL,
    embedding vector(1536)
);

-- 인덱스 생성 (코사인 유사도용)
CREATE INDEX ON report_embeddings
USING ivfflat (embedding vector_cosine_ops);

-- 유사도 검색
SELECT report_id, 1 - (embedding <=> $1) AS similarity
FROM report_embeddings
ORDER BY embedding <=> $1
LIMIT 10;
```
