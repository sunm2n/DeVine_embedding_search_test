"""
100개 리포트 벡터 검색 성능 테스트

측정 항목:
1. 개당 임베딩 생성 시간 (FastAPI → OpenAI)
2. 개당 Spring 서버 저장 시간
3. 100개 저장 후 벡터 검색 시간
"""

import asyncio
import httpx
import time
import random

FASTAPI_URL = "http://localhost:8000"
SPRING_URL = "http://localhost:8080"

# 다양한 프로젝트 생성을 위한 템플릿
TECHS = [
    ("JavaScript", "Express.js", "Node.js 백엔드"),
    ("TypeScript", "React", "프론트엔드 SPA"),
    ("Python", "FastAPI", "Python 백엔드"),
    ("Java", "Spring Boot", "엔터프라이즈 백엔드"),
    ("Kotlin", "Spring", "Kotlin 백엔드"),
    ("Go", "Gin", "Go 마이크로서비스"),
    ("Rust", "Actix", "고성능 시스템"),
    ("Swift", "SwiftUI", "iOS 앱"),
    ("Dart", "Flutter", "크로스플랫폼 앱"),
    ("C#", ".NET", "Windows 애플리케이션"),
]

DOMAINS = [
    "이커머스 플랫폼", "소셜 미디어", "금융 서비스", "헬스케어", "교육 플랫폼",
    "물류 관리", "예약 시스템", "콘텐츠 관리", "채팅 애플리케이션", "데이터 분석",
    "IoT 대시보드", "게임 백엔드", "스트리밍 서비스", "결제 시스템", "인증 서비스",
]

FEATURES = [
    "JWT 인증 및 권한 관리", "실시간 알림 시스템", "파일 업로드 처리",
    "검색 엔진 연동", "캐싱 레이어 구현", "API 게이트웨이",
    "메시지 큐 처리", "배치 작업 스케줄링", "모니터링 대시보드",
    "A/B 테스트 프레임워크", "추천 알고리즘", "데이터 파이프라인",
]


def generate_report(report_id: int) -> tuple[str, dict]:
    """다양한 리포트 생성"""
    tech = TECHS[report_id % len(TECHS)]
    domain = DOMAINS[report_id % len(DOMAINS)]
    features = random.sample(FEATURES, k=3)

    title = f"{domain} - {tech[2]}"
    report = {
        "overview": {
            "summary": f"이 프로젝트는 {domain}을 위한 {tech[2]} 시스템입니다. {tech[0]}와 {tech[1]}을 활용하여 개발되었습니다.",
            "mainTech": f"{tech[0]} 기반 {tech[1]} 프레임워크를 활용한 개발"
        },
        "projectInfo": {
            "techStack": [tech[0], tech[1], "PostgreSQL", "Redis", "Docker"]
        },
        "keyImplementations": [
            {"title": features[0]},
            {"title": features[1]},
            {"title": features[2]},
        ]
    }
    return title, report


async def main():
    print("=" * 70)
    print("100개 리포트 벡터 검색 성능 테스트")
    print("=" * 70)

    # 기존 데이터 개수 확인
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{SPRING_URL}/api/vectors/count")
        initial_count = resp.json().get("count", 0)
        print(f"\n기존 저장된 벡터 수: {initial_count}")

    # 통계 저장
    embedding_times = []
    save_times = []

    print("\n" + "-" * 70)
    print("1단계: 100개 리포트 개별 임베딩 생성 및 저장")
    print("-" * 70)

    async with httpx.AsyncClient(timeout=60.0) as client:
        for i in range(1, 101):
            report_id = initial_count + i
            title, report = generate_report(i)

            # 1. 임베딩 생성 시간 측정
            embed_start = time.time()
            embed_resp = await client.post(
                f"{FASTAPI_URL}/embed",
                json={"report": report}
            )
            embed_time = (time.time() - embed_start) * 1000
            embedding_times.append(embed_time)

            if embed_resp.status_code != 200:
                print(f"[{i}] 임베딩 실패: {embed_resp.text}")
                continue

            vector = embed_resp.json()["vector"]

            # 2. Spring 서버 저장 시간 측정
            save_start = time.time()
            save_resp = await client.post(
                f"{SPRING_URL}/api/vectors/save",
                json={
                    "reportId": report_id,
                    "reportTitle": title,
                    "vector": vector
                }
            )
            save_time = (time.time() - save_start) * 1000
            save_times.append(save_time)

            # 진행 상황 출력 (10개마다)
            if i % 10 == 0:
                avg_embed = sum(embedding_times[-10:]) / 10
                avg_save = sum(save_times[-10:]) / 10
                print(f"[{i:3d}/100] 최근 10개 평균 - 임베딩: {avg_embed:.1f}ms, 저장: {avg_save:.1f}ms")

    # 임베딩/저장 통계
    print("\n" + "-" * 70)
    print("임베딩 및 저장 시간 통계")
    print("-" * 70)
    print(f"임베딩 생성 (OpenAI API):")
    print(f"  평균: {sum(embedding_times)/len(embedding_times):.1f}ms")
    print(f"  최소: {min(embedding_times):.1f}ms")
    print(f"  최대: {max(embedding_times):.1f}ms")
    print(f"\nSpring 서버 저장:")
    print(f"  평균: {sum(save_times)/len(save_times):.1f}ms")
    print(f"  최소: {min(save_times):.1f}ms")
    print(f"  최대: {max(save_times):.1f}ms")

    # 3. 벡터 검색 시간 측정
    print("\n" + "-" * 70)
    print("2단계: 벡터 검색 성능 테스트 (100개 데이터 기준)")
    print("-" * 70)

    async with httpx.AsyncClient(timeout=60.0) as client:
        # 총 벡터 수 확인
        resp = await client.get(f"{SPRING_URL}/api/vectors/count")
        total_count = resp.json().get("count", 0)
        print(f"\n총 저장된 벡터 수: {total_count}")

        # 검색용 쿼리 벡터 생성 (새로운 리포트로)
        _, query_report = generate_report(999)
        resp = await client.post(f"{FASTAPI_URL}/embed", json={"report": query_report})
        query_vector = resp.json()["vector"]

        # 검색 시간 측정 (10회)
        search_times = []
        db_search_times = []

        print("\n검색 테스트 (10회 반복):")
        for i in range(10):
            start = time.time()
            resp = await client.post(
                f"{SPRING_URL}/api/vectors/search",
                json={"vector": query_vector, "limit": 10}
            )
            total_time = (time.time() - start) * 1000
            search_times.append(total_time)

            result = resp.json()
            if result.get("results"):
                db_time = result["results"][0].get("searchTimeMs", 0)
                db_search_times.append(db_time)

            if i == 0:
                print(f"\n검색 결과 (상위 5개):")
                for idx, r in enumerate(result.get("results", [])[:5], 1):
                    print(f"  {idx}. {r['reportTitle']} (유사도: {r['similarity']:.4f})")

        print(f"\n검색 시간 통계 (10회):")
        print(f"  Spring 전체 응답:")
        print(f"    평균: {sum(search_times)/len(search_times):.1f}ms")
        print(f"    최소: {min(search_times):.1f}ms")
        print(f"    최대: {max(search_times):.1f}ms")
        if db_search_times:
            print(f"  pgvector 검색만:")
            print(f"    평균: {sum(db_search_times)/len(db_search_times):.1f}ms")
            print(f"    최소: {min(db_search_times):.1f}ms")
            print(f"    최대: {max(db_search_times):.1f}ms")

    print("\n" + "=" * 70)
    print("테스트 완료")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
