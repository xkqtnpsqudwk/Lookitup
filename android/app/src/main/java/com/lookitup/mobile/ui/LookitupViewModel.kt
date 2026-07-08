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
        )

        if (payload.type == "manual" && payload.content.isBlank()) {
            _uiState.update { it.copy(error = "Manual sources need text content.") }
            return
        }
        if (payload.type != "manual" && payload.url.isBlank()) {
            _uiState.update { it.copy(error = "RSS and website sources need a URL.") }
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
                    notice = "Trusted source added.",
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
