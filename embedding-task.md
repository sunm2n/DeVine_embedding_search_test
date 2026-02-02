네, 아주 실용적인 결정입니다. **"복잡한 추상화는 걷어내고, 유지보수를 위한 최소한의 포장(Wrapper)만 유지한다"**는 기조로 계획을 다시 정리했습니다.

이 문서는 클로드(Claude)나 AI 코딩 어시스턴트에게 입력했을 때 바로 코드를 짜줄 수 있도록 파일 경로, 역할, 핵심 로직을 명확하게 구조화한 .md 파일입니다.

📋 DeVine AI Server: Core Logic Implementation Plan
1. 개요 (Overview)
목표: DeVine 프로젝트의 AI 서버(FastAPI) 내 핵심 로직(Core Logic) 구현.

범위: API 엔드포인트 구현을 제외한 '설정 로드 -> 텍스트 전처리 -> 임베딩 생성' 파이프라인 구축.

설계 원칙:

Wrapper Pattern: 추상 인터페이스(ABC) 대신 단순 클래스(EmbeddingService)로 라이브러리 의존성을 격리.

Mock-Ready: 추후 리포트 생성 로직 연동을 고려한 데이터 구조 사용.

Test-First: API 서버 실행 없이 로직을 검증할 수 있는 독립 테스트 스크립트 작성.

2. 기술 스택 및 환경 (Environment)
Language: Python 3.10+

Framework: FastAPI (구조 잡기용), Pydantic (데이터 검증)

Libraries:

openai: 임베딩 생성 (Async 지원)

pydantic-settings: 환경변수 관리

python-dotenv: .env 파일 로드

3. 프로젝트 구조 (Directory Structure)
Plaintext

devine-ai/
├── .env                  # API Key 및 설정
├── requirements.txt      # 의존성 목록
├── app/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py     # 환경변수 로드 (Pydantic Settings)
│   ├── services/
│   │   ├── __init__.py
│   │   └── embedding_service.py # [Core] OpenAI Wrapping Class
│   └── utils/
│       ├── __init__.py
│       └── text_processor.py    # [Core] JSON -> String 변환 로직
└── test_core.py          # [Test] 로직 검증 스크립트
4. 단계별 구현 가이드 (Implementation Steps)
Step 1: 의존성 및 환경 설정
목표: 프로젝트 환경 구성 및 API 키 관리 준비.

requirements.txt 작성

fastapi, uvicorn, pydantic-settings, openai, python-dotenv 포함.

.env 파일 생성

OPENAI_API_KEY: 실제 키 또는 Dummy 키.

EMBEDDING_MODEL: text-embedding-3-small (기본값).

app/core/config.py 구현

pydantic_settings.BaseSettings를 상속받아 환경변수 로드.

Singleton 패턴처럼 어디서든 settings.OPENAI_API_KEY로 접근 가능하게 설정.

Step 2: 텍스트 전처리 로직 (app/utils/text_processor.py)
목표: 리포트 JSON에서 임베딩 품질을 높일 수 있는 알짜배기 텍스트만 추출하여 병합.

입력: 리포트 JSON (Dict)

출력: 하나의 긴 문자열 (str)

처리 로직:

overview.summary (프로젝트 요약) 추출.

keyImplementations 배열을 순회하며 title과 description 추출.

aiEvaluation (AI 평가) 내용이 있다면 추출.

위 내용들을 \n 문자로 구분하여 하나의 텍스트로 결합.

(선택) projectInfo의 단순 메타데이터(날짜 등)는 임베딩 노이즈가 될 수 있으므로 제외.

Step 3: 임베딩 서비스 Wrapper (app/services/embedding_service.py)
목표: OpenAI 라이브러리 호출 코드를 클래스 하나로 감싸서(Wrapping) 메인 로직을 보호.

Class: EmbeddingService

Method: async def create_embedding(self, text: str) -> List[float]

구현 상세:

생성자(__init__)에서 AsyncOpenAI 클라이언트 초기화.

create_embedding 내부에서 client.embeddings.create 호출.

반환값은 복잡한 OpenAI 객체가 아닌, 순수 List[float] (벡터 배열)만 반환.

에러 발생 시 로그 출력 및 예외 전파.

Step 4: 통합 테스트 스크립트 (test_core.py)
목표: API 서버를 띄우지 않고 핵심 로직이 잘 동작하는지 확인.

테스트 데이터: 실제 리포트와 유사한 구조의 Mock JSON 데이터 정의.

실행 흐름:

text_processor를 통해 Mock JSON -> 텍스트 변환 결과 출력.

EmbeddingService를 통해 텍스트 -> 벡터 변환 수행.

생성된 벡터의 차원 수(Dimension)가 1536인지 검증.

성공/실패 여부 콘솔 출력.

5. 데이터 명세 (Data Specifications)
Input (Report JSON Sample)
이 구조를 파싱할 수 있어야 함

JSON

{
  "overview": {
    "summary": "음악 API 연동 백엔드 시스템..."
  },
  "keyImplementations": [
    {
      "title": "JWT 인증",
      "description": "Access/Refresh Token 구현..."
    }
  ]
}
Output (Vector)
Type: List[float]

Dimension: 1536 (text-embedding-3-small 기준)

6. 개발 체크리스트 (Checklist)
[ ] .env 및 config.py 설정 완료

[ ] text_processor.py에서 JSON 파싱 및 문자열 병합 로직 구현

[ ] embedding_service.py에서 OpenAI API 호출 및 응답 정제 구현

[ ] test_core.py 실행하여 벡터 생성 성공 확인

[ ] (Optional) 벡터 차원 수가 맞는지 확인