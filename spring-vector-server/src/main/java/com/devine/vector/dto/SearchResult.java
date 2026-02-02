package com.devine.vector.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
public class SearchResult {
    private Long reportId;
    private String reportTitle;
    private Double similarity;
    private Long searchTimeMs;
}
