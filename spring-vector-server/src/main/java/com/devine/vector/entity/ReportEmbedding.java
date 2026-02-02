package com.devine.vector.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

@Entity
@Table(name = "report_embeddings")
@Getter
@Setter
@NoArgsConstructor
public class ReportEmbedding {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "report_id", nullable = false)
    private Long reportId;

    @Column(name = "report_title", length = 500)
    private String reportTitle;

    // pgvector는 float[]로 저장, native query로 처리
    @Column(name = "embedding", columnDefinition = "vector(1536)")
    private String embedding;

    @Column(name = "created_at")
    private LocalDateTime createdAt = LocalDateTime.now();

    public ReportEmbedding(Long reportId, String reportTitle, String embedding) {
        this.reportId = reportId;
        this.reportTitle = reportTitle;
        this.embedding = embedding;
    }
}
