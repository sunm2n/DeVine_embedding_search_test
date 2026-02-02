package com.devine.vector.service;

import com.devine.vector.dto.EmbeddingRequest;
import com.devine.vector.dto.SearchRequest;
import com.devine.vector.dto.SearchResult;
import com.devine.vector.repository.ReportEmbeddingRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class VectorService {

    private final ReportEmbeddingRepository repository;

    @Transactional
    public void saveEmbedding(EmbeddingRequest request) {
        String vectorString = vectorToString(request.getVector());
        repository.saveEmbedding(
                request.getReportId(),
                request.getReportTitle(),
                vectorString
        );
        log.info("Saved embedding for reportId: {}", request.getReportId());
    }

    @Transactional(readOnly = true)
    public List<SearchResult> searchSimilar(SearchRequest request) {
        String queryVector = vectorToString(request.getVector());
        log.debug("Query vector (first 50 chars): {}", queryVector.substring(0, Math.min(50, queryVector.length())));

        long startTime = System.currentTimeMillis();
        List<Object[]> results = repository.findSimilarByCosineSimilarity(
                queryVector,
                request.getLimit()
        );
        long endTime = System.currentTimeMillis();
        long searchTime = endTime - startTime;

        log.info("Vector search completed in {}ms, found {} results", searchTime, results.size());

        List<SearchResult> searchResults = new ArrayList<>();
        for (Object[] row : results) {
            searchResults.add(new SearchResult(
                    ((Number) row[0]).longValue(),
                    (String) row[1],
                    ((Number) row[2]).doubleValue(),
                    searchTime
            ));
        }
        return searchResults;
    }

    @Transactional(readOnly = true)
    public long getEmbeddingCount() {
        return repository.countEmbeddings();
    }

    private String vectorToString(List<Double> vector) {
        return "[" + vector.stream()
                .map(String::valueOf)
                .collect(Collectors.joining(",")) + "]";
    }
}
