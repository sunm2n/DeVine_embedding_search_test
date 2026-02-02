package com.devine.vector.dto;

import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
public class SearchRequest {
    private List<Double> vector;
    private Integer limit = 5;
}
