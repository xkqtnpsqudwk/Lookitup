package com.lookitup.mobile.data

import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import com.lookitup.mobile.BuildConfig
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit

class LookitupRepository(
    apiBaseUrl: String = BuildConfig.API_BASE_URL,
) {
    private val api: LookitupApi

    init {
        val json = Json {
            ignoreUnknownKeys = true
        }
        val logging = HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) {
                HttpLoggingInterceptor.Level.BASIC
            } else {
                HttpLoggingInterceptor.Level.NONE
            }
        }
        val client = OkHttpClient.Builder()
            .addInterceptor(logging)
            .build()

        api = Retrofit.Builder()
            .baseUrl(apiBaseUrl)
            .client(client)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
            .create(LookitupApi::class.java)
    }

    suspend fun getSources(): List<SourceDto> = api.getSources()

    suspend fun addSource(payload: SourceCreateDto): SourceDto = api.addSource(payload)

    suspend fun clearSources(): ClearSourcesResponseDto = api.clearSources()

    suspend fun loadSamples(): LoadSamplesResponseDto = api.loadSamples()

    suspend fun search(query: String, sort: String): SearchResponseDto = api.search(query, sort)

    suspend fun summarize(query: String, sort: String, style: String): SummaryResponseDto =
        api.summarize(query, sort, style)
}
