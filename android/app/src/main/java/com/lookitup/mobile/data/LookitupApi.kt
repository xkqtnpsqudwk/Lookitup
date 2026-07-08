package com.lookitup.mobile.data

import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Query

interface LookitupApi {
    @GET("sources")
    suspend fun getSources(): List<SourceDto>

    @POST("sources")
    suspend fun addSource(@Body payload: SourceCreateDto): SourceDto

    @DELETE("sources")
    suspend fun clearSources(): ClearSourcesResponseDto

    @POST("sources/load-samples")
    suspend fun loadSamples(): LoadSamplesResponseDto

    @GET("search")
    suspend fun search(
        @Query("q") query: String,
        @Query("sort") sort: String,
    ): SearchResponseDto

    @GET("summarize")
    suspend fun summarize(
        @Query("q") query: String,
        @Query("sort") sort: String,
        @Query("style") style: String,
    ): SummaryResponseDto
}
