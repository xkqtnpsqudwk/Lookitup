package com.lookitup.mobile.data

import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.Part
import retrofit2.http.POST
import retrofit2.http.Query
import okhttp3.MultipartBody
import okhttp3.RequestBody

interface LookitupApi {
    @GET("sources")
    suspend fun getSources(): List<SourceDto>

    @POST("sources")
    suspend fun addSource(@Body payload: SourceCreateDto): SourceDto

    @Multipart
    @POST("sources/pdf")
    suspend fun addPdfSource(
        @Part file: MultipartBody.Part,
        @Part("name") name: RequestBody,
    ): SourceDto

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
