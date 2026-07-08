package com.lookitup.mobile.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class SourceDto(
    val id: String,
    val name: String,
    val type: String,
    val url: String = "",
    @SerialName("created_at") val createdAt: String,
    @SerialName("item_count") val itemCount: Int,
)

@Serializable
data class SourceCreateDto(
    val name: String = "",
    val type: String,
    val url: String = "",
    val content: String = "",
    @SerialName("date_from") val dateFrom: String = "",
    @SerialName("date_to") val dateTo: String = "",
)

@Serializable
data class LoadSamplesResponseDto(
    val added: Int,
    val sources: List<SourceDto>,
)

@Serializable
data class ClearSourcesResponseDto(
    val status: String,
    val removed: Int,
)

@Serializable
data class SearchResultDto(
    val id: String,
    @SerialName("source_id") val sourceId: String,
    @SerialName("source_name") val sourceName: String,
    @SerialName("source_type") val sourceType: String,
    val title: String,
    val url: String = "",
    val timestamp: String? = null,
    val excerpt: String,
    @SerialName("match_count") val matchCount: Int,
    val score: Int,
    val recency: String,
    val explanation: String,
)

@Serializable
data class SearchResponseDto(
    val query: String,
    val count: Int,
    val results: List<SearchResultDto>,
)

@Serializable
data class SummaryResponseDto(
    val query: String,
    val summary: String,
    val model: String,
    val style: String,
    @SerialName("used_sources") val usedSources: List<String>,
    @SerialName("based_on") val basedOn: Int,
    @SerialName("grounded_in") val groundedIn: Int,
)
