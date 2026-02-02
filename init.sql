-- pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 임베딩 테이블 생성
CREATE TABLE IF NOT EXISTS report_embeddings (
    id BIGSERIAL PRIMARY KEY,
    report_id BIGINT NOT NULL,
    report_title VARCHAR(500),
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 코사인 유사도 검색을 위한 인덱스 (IVFFlat)
-- 데이터가 적을 때는 lists 값을 작게 설정
CREATE INDEX IF NOT EXISTS idx_embedding_cosine
ON report_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 10);

-- L2 거리 검색을 위한 인덱스 (선택적)
CREATE INDEX IF NOT EXISTS idx_embedding_l2
ON report_embeddings
USING ivfflat (embedding vector_l2_ops)
WITH (lists = 10);
