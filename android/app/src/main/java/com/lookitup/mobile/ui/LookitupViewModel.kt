package com.lookitup.mobile.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.lookitup.mobile.data.LookitupRepository
import com.lookitup.mobile.data.SearchResultDto
import com.lookitup.mobile.data.SourceCreateDto
import com.lookitup.mobile.data.SourceDto
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class LookitupUiState(
    val sources: List<SourceDto> = emptyList(),
    val results: List<SearchResultDto> = emptyList(),
    val query: String = "Iran Israel rockets",
    val sort: String = "relevance",
    val summary: String = "",
    val sourceType: String = "manual",
    val sourceName: String = "",
    val sourceUrl: String = "",
    val sourceContent: String = "",
    val sourceDateFrom: String = "",
    val sourceDateTo: String = "",
    val sourcePdfUri: String = "",
    val sourcePdfFileName: String = "",
    val isLoading: Boolean = false,
    val error: String = "",
    val notice: String = "",
)

class LookitupViewModel(
    private val repository: LookitupRepository = LookitupRepository(),
) : ViewModel() {
    private val _uiState = MutableStateFlow(LookitupUiState())
    val uiState: StateFlow<LookitupUiState> = _uiState.asStateFlow()

    init {
        refreshSources()
    }

    fun refreshSources() {
        launchWithLoading {
            val sources = repository.getSources()
            _uiState.update { it.copy(sources = sources, notice = "") }
        }
    }

    fun loadSamples() {
        launchWithLoading {
            repository.loadSamples()
            val sources = repository.getSources()
            _uiState.update {
                it.copy(
                    sources = sources,
                    notice = "Sample sources loaded.",
                )
            }
        }
    }

    fun clearSources() {
        launchWithLoading {
            repository.clearSources()
            _uiState.update {
                it.copy(
                    sources = emptyList(),
                    results = emptyList(),
                    summary = "",
                    notice = "Trusted sources cleared.",
                )
            }
        }
    }

    fun search() {
        val state = _uiState.value
        if (state.query.isBlank()) {
            _uiState.update { it.copy(error = "Enter a topic or claim first.") }
            return
        }
        launchWithLoading {
            val response = repository.search(state.query.trim(), state.sort)
            _uiState.update {
                it.copy(
                    results = response.results,
                    summary = "",
                    notice = if (response.results.isEmpty()) {
                        "No trusted result found."
                    } else {
                        "${response.count} trusted result card(s) found."
                    },
                )
            }
        }
    }

    fun summarize() {
        val state = _uiState.value
        if (state.query.isBlank()) {
            _uiState.update { it.copy(error = "Enter a topic or claim first.") }
            return
        }
        launchWithLoading {
            val response = repository.summarize(state.query.trim(), state.sort, "paragraph")
            _uiState.update {
                it.copy(
                    summary = response.summary,
                    notice = "Summary generated from ${response.groundedIn} trusted result(s).",
                )
            }
        }
    }

    fun addSource() {
        val state = _uiState.value
        val payload = SourceCreateDto(
            name = state.sourceName.trim(),
            type = state.sourceType,
            url = if (state.sourceType == "manual") "" else state.sourceUrl.trim(),
            content = if (state.sourceType == "manual") state.sourceContent.trim() else "",
            dateFrom = if (state.sourceType == "rss") state.sourceDateFrom else "",
            dateTo = if (state.sourceType == "rss") state.sourceDateTo else "",
        )

        if (payload.type == "manual" && payload.content.isBlank()) {
            _uiState.update { it.copy(error = "Manual sources need text content.") }
            return
        }
        if (payload.type == "pdf") {
            _uiState.update { it.copy(error = "Choose a PDF file to upload.") }
            return
        }
        if ((payload.type == "rss" || payload.type == "website") && payload.url.isBlank()) {
            _uiState.update { it.copy(error = "RSS and website sources need a URL.") }
            return
        }
        if (payload.type == "rss" && payload.dateFrom.isNotBlank() && payload.dateTo.isNotBlank() && payload.dateFrom > payload.dateTo) {
            _uiState.update { it.copy(error = "RSS start date must be before the end date.") }
            return
        }

        launchWithLoading {
            repository.addSource(payload)
            val sources = repository.getSources()
            _uiState.update {
                it.copy(
                    sources = sources,
                    sourceName = "",
                    sourceUrl = "",
                    sourceContent = "",
                    sourceDateFrom = "",
                    sourceDateTo = "",
                    sourcePdfUri = "",
                    sourcePdfFileName = "",
                    notice = "Trusted source added.",
                )
            }
        }
    }

    fun addPdfSource(fileBytes: ByteArray, fileName: String) {
        val state = _uiState.value
        if (fileBytes.isEmpty()) {
            _uiState.update { it.copy(error = "The selected PDF is empty.") }
            return
        }
        launchWithLoading {
            repository.addPdfSource(fileBytes, fileName, state.sourceName.trim())
            val sources = repository.getSources()
            _uiState.update {
                it.copy(
                    sources = sources,
                    sourceName = "",
                    sourcePdfUri = "",
                    sourcePdfFileName = "",
                    notice = "PDF source uploaded.",
                )
            }
        }
    }

    fun setQuery(value: String) {
        _uiState.update { it.copy(query = value, error = "", notice = "") }
    }

    fun setSort(value: String) {
        _uiState.update { it.copy(sort = value, error = "", notice = "") }
    }

    fun setSourceType(value: String) {
        _uiState.update { it.copy(sourceType = value, error = "", notice = "") }
    }

    fun setSourceName(value: String) {
        _uiState.update { it.copy(sourceName = value, error = "", notice = "") }
    }

    fun setSourceUrl(value: String) {
        _uiState.update { it.copy(sourceUrl = value, error = "", notice = "") }
    }

    fun setSourceContent(value: String) {
        _uiState.update { it.copy(sourceContent = value, error = "", notice = "") }
    }

    fun setSourceDateFrom(value: String) {
        _uiState.update { it.copy(sourceDateFrom = value, error = "", notice = "") }
    }

    fun setSourceDateTo(value: String) {
        _uiState.update { it.copy(sourceDateTo = value, error = "", notice = "") }
    }

    fun setSourcePdfFile(uri: String, fileName: String) {
        _uiState.update {
            it.copy(
                sourcePdfUri = uri,
                sourcePdfFileName = fileName,
                error = "",
                notice = "",
            )
        }
    }

    fun setSourceError(message: String) {
        _uiState.update { it.copy(error = message, notice = "") }
    }

    private fun launchWithLoading(block: suspend () -> Unit) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = "", notice = "") }
            try {
                block()
            } catch (error: Exception) {
                _uiState.update {
                    it.copy(
                        error = error.message ?: "Request failed.",
                    )
                }
            } finally {
                _uiState.update { it.copy(isLoading = false) }
            }
        }
    }
}
