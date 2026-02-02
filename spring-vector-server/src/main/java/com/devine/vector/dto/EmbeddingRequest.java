package com.devine.vector.dto;

import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
public class EmbeddingRequest {
    private Long reportId;
    private String reportTitle;
    private List<Double> vector;
}
