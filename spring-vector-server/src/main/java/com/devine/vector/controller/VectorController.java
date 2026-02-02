package com.devine.vector.controller;

import com.devine.vector.dto.EmbeddingRequest;
import com.devine.vector.dto.SearchRequest;
import com.devine.vector.dto.SearchResult;
import com.devine.vector.service.VectorService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/vectors")
@RequiredArgsConstructor
public class VectorController {

    private final VectorService vectorService;

    @PostMapping("/save")
    public ResponseEntity<Map<String, Object>> saveEmbedding(@RequestBody EmbeddingRequest request) {
        try {
            long startTime = System.currentTimeMillis();
            vectorService.saveEmbedding(request);
            long duration = System.currentTimeMillis() - startTime;

            return ResponseEntity.ok(Map.of(
                    "success", true,
                    "reportId", request.getReportId(),
                    "saveTimeMs", duration
            ));
        } catch (Exception e) {
            log.error("Save failed", e);
            return ResponseEntity.internalServerError().body(Map.of(
                    "success", false,
                    "error", e.getMessage() != null ? e.getMessage() : "Unknown error",
                    "errorType", e.getClass().getSimpleName()
            ));
        }
    }

    @PostMapping("/search")
    public ResponseEntity<Map<String, Object>> searchSimilar(@RequestBody SearchRequest request) {
        try {
            log.info("Search request received, vector size: {}", request.getVector().size());
            long startTime = System.currentTimeMillis();
            List<SearchResult> results = vectorService.searchSimilar(request);
            long totalDuration = System.currentTimeMillis() - startTime;

            return ResponseEntity.ok(Map.of(
                    "success", true,
                    "results", results,
                    "totalTimeMs", totalDuration,
                    "resultCount", results.size()
            ));
        } catch (Exception e) {
            log.error("Search failed", e);
            return ResponseEntity.internalServerError().body(Map.of(
                    "success", false,
                    "error", e.getMessage() != null ? e.getMessage() : "Unknown error"
            ));
        }
    }

    @GetMapping("/count")
    public ResponseEntity<Map<String, Object>> getCount() {
        long count = vectorService.getEmbeddingCount();
        return ResponseEntity.ok(Map.of(
                "count", count
        ));
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        return ResponseEntity.ok(Map.of(
                "status", "healthy",
                "service", "Spring Vector Server"
        ));
    }
}
