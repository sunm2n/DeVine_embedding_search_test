"""
벡터 검색 성능 테스트 스크립트

플로우:
1. FastAPI 서버에서 임베딩 생성
2. Spring 서버로 벡터 저장
3. 벡터 검색 시간 측정
"""

import asyncio
import httpx
import time
import json
from typing import Optional

FASTAPI_URL = "http://localhost:8000"
SPRING_URL = "http://localhost:8080"

# 테스트용 샘플 리포트들
SAMPLE_REPORTS = [
    {
        "report_id": 1,
        "title": "음악 API 백엔드",
        "report": {
            "overview": {
                "summary": "이 프로젝트는 다양한 외부 음악 API(Last.fm, iTunes, Spotify)와 연동하여 음악 정보를 제공하는 백엔드 시스템입니다.",
                "mainTech": "JavaScript 기반 Express.js 프레임워크를 활용한 백엔드 API 서버 개발"
            },
            "projectInfo": {
                "techStack": ["JavaScript", "Express.js", "Prisma", "OpenAI API", "AWS SDK (S3)"]
            },
            "keyImplementations": [
                {"title": "외부 음악 서비스 API 통합 및 데이터 관리"},
                {"title": "사용자 인증 및 권한 부여 시스템"},
                {"title": "AI 기반 음악 추천 및 사용자 맞춤형 서비스"}
            ]
        }
    },
    {
        "report_id": 2,
        "title": "React 프론트엔드 대시보드",
        "report": {
            "overview": {
                "summary": "관리자용 대시보드 애플리케이션으로, 실시간 데이터 시각화와 사용자 관리 기능을 제공합니다.",
                "mainTech": "React와 TypeScript를 사용한 SPA 프론트엔드 개발"
            },
            "projectInfo": {
                "techStack": ["TypeScript", "React", "Redux", "Chart.js", "TailwindCSS"]
            },
            "keyImplementations": [
                {"title": "실시간 데이터 시각화 대시보드"},
                {"title": "사용자 권한 기반 라우팅"},
                {"title": "반응형 UI 컴포넌트 시스템"}
            ]
        }
    },
    {
        "report_id": 3,
        "title": "Spring Boot 마이크로서비스",
        "report": {
            "overview": {
                "summary": "주문 관리 시스템을 위한 마이크로서비스 아키텍처 기반 백엔드 서비스입니다.",
                "mainTech": "Spring Boot와 Spring Cloud를 활용한 마이크로서비스 개발"
            },
            "projectInfo": {
                "techStack": ["Java", "Spring Boot", "Spring Cloud", "Kafka", "PostgreSQL"]
            },
            "keyImplementations": [
                {"title": "이벤트 기반 마이크로서비스 통신"},
                {"title": "분산 트랜잭션 관리"},
                {"title": "API Gateway 및 서비스 디스커버리"}
            ]
        }
    },
    {
        "report_id": 4,
        "title": "Python ML 파이프라인",
        "report": {
            "overview": {
                "summary": "머신러닝 모델 학습 및 배포를 위한 자동화된 파이프라인 시스템입니다.",
                "mainTech": "Python 기반 MLOps 파이프라인 구축"
            },
            "projectInfo": {
                "techStack": ["Python", "TensorFlow", "MLflow", "Airflow", "Docker"]
            },
            "keyImplementations": [
                {"title": "자동화된 모델 학습 파이프라인"},
                {"title": "모델 버전 관리 및 실험 추적"},
                {"title": "A/B 테스트 기반 모델 배포"}
            ]
        }
    },
    {
        "report_id": 5,
        "title": "Flutter 모바일 앱",
        "report": {
            "overview": {
                "summary": "iOS와 Android를 지원하는 크로스플랫폼 소셜 미디어 애플리케이션입니다.",
                "mainTech": "Flutter와 Dart를 사용한 크로스플랫폼 모바일 앱 개발"
            },
            "projectInfo": {
                "techStack": ["Dart", "Flutter", "Firebase", "Provider", "GetX"]
            },
            "keyImplementations": [
                {"title": "실시간 채팅 및 알림 시스템"},
                {"title": "이미지/동영상 업로드 및 처리"},
                {"title": "소셜 피드 무한 스크롤"}
            ]
        }
    }
]


async def get_embedding(client: httpx.AsyncClient, report: dict) -> Optional[list]:
    """FastAPI 서버에서 임베딩 생성"""
    try:
        response = await client.post(
            f"{FASTAPI_URL}/embed",
            json={"report": report},
            timeout=30.0
        )
        if response.status_code == 200:
            return response.json()["vector"]
        else:
            print(f"Embedding error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Embedding request failed: {e}")
        return None


async def save_embedding(client: httpx.AsyncClient, report_id: int, title: str, vector: list) -> dict:
    """Spring 서버에 벡터 저장"""
    try:
        response = await client.post(
            f"{SPRING_URL}/api/vectors/save",
            json={
                "reportId": report_id,
                "reportTitle": title,
                "vector": vector
            },
            timeout=30.0
        )
        return response.json()
    except Exception as e:
        print(f"Save request failed: {e}")
        return {"success": False, "error": str(e)}


async def search_similar(client: httpx.AsyncClient, vector: list, limit: int = 5) -> dict:
    """Spring 서버에서 유사도 검색"""
    try:
        response = await client.post(
            f"{SPRING_URL}/api/vectors/search",
            json={
                "vector": vector,
                "limit": limit
            },
            timeout=30.0
        )
        return response.json()
    except Exception as e:
        print(f"Search request failed: {e}")
        return {"success": False, "error": str(e)}


async def get_count(client: httpx.AsyncClient) -> int:
    """저장된 벡터 수 조회"""
    try:
        response = await client.get(f"{SPRING_URL}/api/vectors/count", timeout=10.0)
        return response.json().get("count", 0)
    except:
        return 0


async def main():
    print("=" * 60)
    print("벡터 검색 성능 테스트")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # 1. 현재 저장된 벡터 수 확인
        count = await get_count(client)
        print(f"\n현재 저장된 벡터 수: {count}")

        # 2. 샘플 데이터로 임베딩 생성 및 저장
        print("\n" + "-" * 60)
        print("1단계: 임베딩 생성 및 저장")
        print("-" * 60)

        embeddings = {}
        for sample in SAMPLE_REPORTS:
            report_id = sample["report_id"]
            title = sample["title"]

            # 임베딩 생성
            start = time.time()
            vector = await get_embedding(client, sample["report"])
            embed_time = (time.time() - start) * 1000

            if vector:
                embeddings[report_id] = vector
                print(f"[{report_id}] {title}")
                print(f"    임베딩 생성: {embed_time:.1f}ms (차원: {len(vector)})")

                # 저장
                start = time.time()
                result = await save_embedding(client, report_id, title, vector)
                save_time = (time.time() - start) * 1000
                print(f"    DB 저장: {save_time:.1f}ms")
            else:
                print(f"[{report_id}] {title} - 임베딩 실패!")

        # 3. 벡터 검색 테스트
        print("\n" + "-" * 60)
        print("2단계: 벡터 검색 성능 테스트")
        print("-" * 60)

        # 검색 쿼리로 사용할 임베딩 (첫 번째 리포트 사용)
        if 1 in embeddings:
            query_vector = embeddings[1]

            # 여러 번 검색해서 평균 시간 측정
            search_times = []
            for i in range(5):
                start = time.time()
                result = await search_similar(client, query_vector, limit=5)
                search_time = (time.time() - start) * 1000
                search_times.append(search_time)

                if i == 0:  # 첫 번째 결과만 출력
                    print(f"\n검색 쿼리: '음악 API 백엔드' 리포트와 유사한 프로젝트")
                    print(f"DB 내 벡터 검색 시간: {result.get('results', [{}])[0].get('searchTimeMs', 0)}ms")
                    print(f"전체 API 응답 시간: {search_time:.1f}ms")
                    print(f"\n검색 결과 (상위 5개):")
                    for idx, r in enumerate(result.get("results", []), 1):
                        print(f"  {idx}. {r['reportTitle']} (유사도: {r['similarity']:.4f})")

            avg_time = sum(search_times) / len(search_times)
            min_time = min(search_times)
            max_time = max(search_times)

            print(f"\n검색 시간 통계 (5회 측정):")
            print(f"  평균: {avg_time:.1f}ms")
            print(f"  최소: {min_time:.1f}ms")
            print(f"  최대: {max_time:.1f}ms")

        # 4. 최종 통계
        count = await get_count(client)
        print("\n" + "-" * 60)
        print("최종 결과")
        print("-" * 60)
        print(f"저장된 총 벡터 수: {count}")


if __name__ == "__main__":
    asyncio.run(main())
