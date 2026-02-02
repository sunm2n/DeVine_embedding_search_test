package com.devine.vector.repository;

import com.devine.vector.entity.ReportEmbedding;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ReportEmbeddingRepository extends JpaRepository<ReportEmbedding, Long> {

    // Native query로 벡터 저장 (JPA에서 vector 타입 직접 처리가 어려움)
    @Modifying(clearAutomatically = true, flushAutomatically = true)
    @Query(value = """
        INSERT INTO report_embeddings (report_id, report_title, embedding, created_at)
        VALUES (:reportId, :reportTitle, CAST(:embedding AS vector), CURRENT_TIMESTAMP)
        """, nativeQuery = true)
    void saveEmbedding(
            @Param("reportId") Long reportId,
            @Param("reportTitle") String reportTitle,
            @Param("embedding") String embedding
    );

    // 코사인 유사도 검색 (1 - 거리 = 유사도)
    @Query(value = """
        SELECT re.report_id, re.report_title,
               1 - (re.embedding <=> CAST(:queryVector AS vector)) as similarity
        FROM report_embeddings re
        ORDER BY re.embedding <=> CAST(:queryVector AS vector)
        LIMIT :limitCount
        """, nativeQuery = true)
    List<Object[]> findSimilarByCosineSimilarity(
            @Param("queryVector") String queryVector,
            @Param("limitCount") int limitCount
    );

    // L2 거리 검색
    @Query(value = """
        SELECT re.report_id, re.report_title,
               re.embedding <-> CAST(:queryVector AS vector) as distance
        FROM report_embeddings re
        ORDER BY re.embedding <-> CAST(:queryVector AS vector)
        LIMIT :limitCount
        """, nativeQuery = true)
    List<Object[]> findSimilarByL2Distance(
            @Param("queryVector") String queryVector,
            @Param("limitCount") int limitCount
    );

    @Query(value = "SELECT COUNT(*) FROM report_embeddings", nativeQuery = true)
    long countEmbeddings();
}
