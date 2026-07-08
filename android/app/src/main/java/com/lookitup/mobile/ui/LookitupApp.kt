package com.lookitup.mobile.ui

import android.app.DatePickerDialog
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.lookitup.mobile.data.SearchResultDto
import com.lookitup.mobile.data.SourceDto
import java.util.Calendar

private val LookitupColors = lightColorScheme(
    primary = Color(0xFF0F766E),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFCCFBF1),
    onPrimaryContainer = Color(0xFF115E59),
    secondary = Color(0xFF334155),
    background = Color(0xFFF8FAFC),
    surface = Color.White,
    surfaceVariant = Color(0xFFF1F5F9),
    outline = Color(0xFFCBD5E1),
    error = Color(0xFFB91C1C),
)

@Composable
fun LookitupApp(viewModel: LookitupViewModel = viewModel()) {
    val state by viewModel.uiState.collectAsState()

    MaterialTheme(colorScheme = LookitupColors) {
        Surface(
            modifier = Modifier.fillMaxSize(),
            color = MaterialTheme.colorScheme.background,
        ) {
            LookitupScreen(
                state = state,
                onLoadSamples = viewModel::loadSamples,
                onClearSources = viewModel::clearSources,
                onRefreshSources = viewModel::refreshSources,
                onSearch = viewModel::search,
                onSummarize = viewModel::summarize,
                onQueryChange = viewModel::setQuery,
                onSortChange = viewModel::setSort,
                onSourceTypeChange = viewModel::setSourceType,
                onSourceNameChange = viewModel::setSourceName,
                onSourceUrlChange = viewModel::setSourceUrl,
                onSourceContentChange = viewModel::setSourceContent,
                onSourceDateFromChange = viewModel::setSourceDateFrom,
                onSourceDateToChange = viewModel::setSourceDateTo,
                onAddSource = viewModel::addSource,
            )
        }
    }
}

@Composable
private fun LookitupScreen(
    state: LookitupUiState,
    onLoadSamples: () -> Unit,
    onClearSources: () -> Unit,
    onRefreshSources: () -> Unit,
    onSearch: () -> Unit,
    onSummarize: () -> Unit,
    onQueryChange: (String) -> Unit,
    onSortChange: (String) -> Unit,
    onSourceTypeChange: (String) -> Unit,
    onSourceNameChange: (String) -> Unit,
    onSourceUrlChange: (String) -> Unit,
    onSourceContentChange: (String) -> Unit,
    onSourceDateFromChange: (String) -> Unit,
    onSourceDateToChange: (String) -> Unit,
    onAddSource: () -> Unit,
) {
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            HeaderCard()
        }

        if (state.error.isNotBlank()) {
            item {
                StatusCard(text = state.error, isError = true)
            }
        }

        if (state.notice.isNotBlank()) {
            item {
                StatusCard(text = state.notice, isError = false)
            }
        }

        item {
            SourcePanel(
                state = state,
                onLoadSamples = onLoadSamples,
                onClearSources = onClearSources,
                onRefreshSources = onRefreshSources,
                onSourceTypeChange = onSourceTypeChange,
                onSourceNameChange = onSourceNameChange,
                onSourceUrlChange = onSourceUrlChange,
                onSourceContentChange = onSourceContentChange,
                onSourceDateFromChange = onSourceDateFromChange,
                onSourceDateToChange = onSourceDateToChange,
                onAddSource = onAddSource,
            )
        }

        item {
            SearchPanel(
                state = state,
                onQueryChange = onQueryChange,
                onSortChange = onSortChange,
                onSearch = onSearch,
                onSummarize = onSummarize,
            )
        }

        if (state.summary.isNotBlank()) {
            item {
                SummaryCard(summary = state.summary)
            }
        }

        item {
            Text(
                text = "Trusted Result Cards",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
            )
        }

        if (state.results.isEmpty()) {
            item {
                EmptyResultsCard()
            }
        } else {
            items(state.results, key = { it.id }) { result ->
                ResultCard(result = result)
            }
        }
    }
}

@Composable
private fun HeaderCard() {
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(
                text = "Lookitup",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Black,
            )
            Text(
                text = "Having a doubt? Just Lookitup.",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.secondary,
            )
            Text(
                text = "Search only inside sources you trust. Journalists decide.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.secondary,
            )
        }
    }
}

@Composable
private fun StatusCard(text: String, isError: Boolean) {
    val background = if (isError) Color(0xFFFEF2F2) else Color(0xFFECFDF5)
    val content = if (isError) Color(0xFF991B1B) else Color(0xFF14532D)
    Card(colors = CardDefaults.cardColors(containerColor = background)) {
        Text(
            text = text,
            color = content,
            modifier = Modifier.padding(12.dp),
            style = MaterialTheme.typography.bodyMedium,
        )
    }
}

@Composable
private fun SourcePanel(
    state: LookitupUiState,
    onLoadSamples: () -> Unit,
    onClearSources: () -> Unit,
    onRefreshSources: () -> Unit,
    onSourceTypeChange: (String) -> Unit,
    onSourceNameChange: (String) -> Unit,
    onSourceUrlChange: (String) -> Unit,
    onSourceContentChange: (String) -> Unit,
    onSourceDateFromChange: (String) -> Unit,
    onSourceDateToChange: (String) -> Unit,
    onAddSource: () -> Unit,
) {
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            SectionTitle(
                eyebrow = "Step 1",
                title = "Trusted sources",
                caption = "${state.sources.size} source(s) loaded",
            )

            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(
                    enabled = !state.isLoading,
                    onClick = onLoadSamples,
                ) {
                    Text("Load samples")
                }
                OutlinedButton(
                    enabled = !state.isLoading,
                    onClick = onRefreshSources,
                ) {
                    Text("Refresh")
                }
                TextButton(
                    enabled = !state.isLoading && state.sources.isNotEmpty(),
                    onClick = onClearSources,
                ) {
                    Text("Clear")
                }
            }

            SourceCreateForm(
                state = state,
                onSourceTypeChange = onSourceTypeChange,
                onSourceNameChange = onSourceNameChange,
                onSourceUrlChange = onSourceUrlChange,
                onSourceContentChange = onSourceContentChange,
                onSourceDateFromChange = onSourceDateFromChange,
                onSourceDateToChange = onSourceDateToChange,
                onAddSource = onAddSource,
            )

            HorizontalDivider(color = MaterialTheme.colorScheme.outline)

            if (state.sources.isEmpty()) {
                Text(
                    text = "No trusted sources yet. Load sample sources to try the app quickly.",
                    color = MaterialTheme.colorScheme.secondary,
                    style = MaterialTheme.typography.bodyMedium,
                )
            } else {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    state.sources.take(4).forEach { source ->
                        SourceRow(source = source)
                    }
                    if (state.sources.size > 4) {
                        Text(
                            text = "+${state.sources.size - 4} more source(s)",
                            color = MaterialTheme.colorScheme.secondary,
                            style = MaterialTheme.typography.bodySmall,
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun SourceCreateForm(
    state: LookitupUiState,
    onSourceTypeChange: (String) -> Unit,
    onSourceNameChange: (String) -> Unit,
    onSourceUrlChange: (String) -> Unit,
    onSourceContentChange: (String) -> Unit,
    onSourceDateFromChange: (String) -> Unit,
    onSourceDateToChange: (String) -> Unit,
    onAddSource: () -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(
            text = "Add trusted source",
            fontWeight = FontWeight.Bold,
            style = MaterialTheme.typography.titleMedium,
        )
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            SourceTypeButton("manual", "Manual", state.sourceType, onSourceTypeChange)
            SourceTypeButton("rss", "RSS", state.sourceType, onSourceTypeChange)
            SourceTypeButton("website", "Website", state.sourceType, onSourceTypeChange)
        }
        OutlinedTextField(
            value = state.sourceName,
            onValueChange = onSourceNameChange,
            modifier = Modifier.fillMaxWidth(),
            label = { Text("Display name") },
            singleLine = true,
        )
        if (state.sourceType == "manual") {
            OutlinedTextField(
                value = state.sourceContent,
                onValueChange = onSourceContentChange,
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 96.dp),
                label = { Text("Trusted text") },
                minLines = 4,
            )
        } else {
            OutlinedTextField(
                value = state.sourceUrl,
                onValueChange = onSourceUrlChange,
                modifier = Modifier.fillMaxWidth(),
                label = { Text("URL") },
                singleLine = true,
            )
            if (state.sourceType == "rss") {
                Text(
                    text = "Optional RSS date range",
                    fontWeight = FontWeight.Bold,
                    style = MaterialTheme.typography.bodyMedium,
                )
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    DatePickerButton(
                        label = "From",
                        value = state.sourceDateFrom,
                        onDateSelected = onSourceDateFromChange,
                    )
                    DatePickerButton(
                        label = "To",
                        value = state.sourceDateTo,
                        onDateSelected = onSourceDateToChange,
                    )
                }
                if (state.sourceDateFrom.isNotBlank() || state.sourceDateTo.isNotBlank()) {
                    TextButton(
                        onClick = {
                            onSourceDateFromChange("")
                            onSourceDateToChange("")
                        },
                    ) {
                        Text("Clear dates")
                    }
                }
            }
        }
        Button(
            enabled = !state.isLoading,
            onClick = onAddSource,
        ) {
            Text("Add source")
        }
    }
}

@Composable
private fun DatePickerButton(
    label: String,
    value: String,
    onDateSelected: (String) -> Unit,
) {
    val context = LocalContext.current
    OutlinedButton(
        onClick = {
            val calendar = calendarFromIsoDate(value)
            DatePickerDialog(
                context,
                { _, year, month, dayOfMonth ->
                    onDateSelected("%04d-%02d-%02d".format(year, month + 1, dayOfMonth))
                },
                calendar.get(Calendar.YEAR),
                calendar.get(Calendar.MONTH),
                calendar.get(Calendar.DAY_OF_MONTH),
            ).show()
        },
    ) {
        Text(if (value.isBlank()) label else "$label: $value")
    }
}

private fun calendarFromIsoDate(value: String): Calendar {
    val calendar = Calendar.getInstance()
    val parts = value.split("-")
    if (parts.size == 3) {
        val year = parts[0].toIntOrNull()
        val month = parts[1].toIntOrNull()
        val day = parts[2].toIntOrNull()
        if (year != null && month != null && day != null) {
            calendar.set(year, month - 1, day)
        }
    }
    return calendar
}

@Composable
private fun SourceTypeButton(
    value: String,
    label: String,
    selectedValue: String,
    onSelect: (String) -> Unit,
) {
    if (selectedValue == value) {
        Button(onClick = { onSelect(value) }) {
            Text(label)
        }
    } else {
        OutlinedButton(onClick = { onSelect(value) }) {
            Text(label)
        }
    }
}

@Composable
private fun SourceRow(source: SourceDto) {
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            Text(
                text = source.name,
                fontWeight = FontWeight.Bold,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
            Text(
                text = "${source.type.uppercase()} - ${source.itemCount} item(s)",
                color = MaterialTheme.colorScheme.secondary,
                style = MaterialTheme.typography.bodySmall,
            )
        }
    }
}

@Composable
private fun SearchPanel(
    state: LookitupUiState,
    onQueryChange: (String) -> Unit,
    onSortChange: (String) -> Unit,
    onSearch: () -> Unit,
    onSummarize: () -> Unit,
) {
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            SectionTitle(
                eyebrow = "Step 2",
                title = "Search a topic",
                caption = "Search runs only against trusted sources on the backend.",
            )
            OutlinedTextField(
                value = state.query,
                onValueChange = onQueryChange,
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Topic, keyword, event, or claim") },
                singleLine = true,
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                SourceTypeButton("relevance", "Relevance", state.sort, onSortChange)
                SourceTypeButton("newest", "Newest", state.sort, onSortChange)
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(
                    enabled = !state.isLoading && state.sources.isNotEmpty(),
                    onClick = onSearch,
                ) {
                    Text(if (state.isLoading) "Working..." else "Search")
                }
                OutlinedButton(
                    enabled = !state.isLoading && state.results.isNotEmpty(),
                    onClick = onSummarize,
                ) {
                    Text("Summarize")
                }
            }
        }
    }
}

@Composable
private fun SectionTitle(eyebrow: String, title: String, caption: String) {
    Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
        Text(
            text = eyebrow.uppercase(),
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.primary,
            fontWeight = FontWeight.Black,
        )
        Text(
            text = title,
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Bold,
        )
        Text(
            text = caption,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.secondary,
        )
    }
}

@Composable
private fun SummaryCard(summary: String) {
    Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFECFDF5))) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(
                text = "Grounded summary",
                fontWeight = FontWeight.Bold,
                color = Color(0xFF14532D),
            )
            SelectionContainer {
                Text(
                    text = summary,
                    color = Color(0xFF14532D),
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }
    }
}

@Composable
private fun EmptyResultsCard() {
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Text(
                text = "Run a search to review trusted results.",
                fontWeight = FontWeight.Bold,
            )
            Text(
                text = "No result found does not mean the claim is false. It only means Lookitup could not find it inside your trusted sources.",
                color = MaterialTheme.colorScheme.secondary,
                style = MaterialTheme.typography.bodyMedium,
            )
        }
    }
}

@Composable
private fun ResultCard(result: SearchResultDto) {
    Card(
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(
                text = "Trusted Result Card",
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.Black,
                style = MaterialTheme.typography.labelLarge,
            )
            Text(
                text = result.title,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
            )
            Text(
                text = "${result.sourceName} - ${result.sourceType.uppercase()} - ${result.recency}",
                color = MaterialTheme.colorScheme.secondary,
                style = MaterialTheme.typography.bodySmall,
            )
            SelectionContainer {
                Text(
                    text = result.excerpt,
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
            Text(
                text = "Matches: ${result.matchCount}  Score: ${result.score}",
                color = MaterialTheme.colorScheme.secondary,
                style = MaterialTheme.typography.bodySmall,
            )
            Text(
                text = result.explanation,
                color = MaterialTheme.colorScheme.primary,
                style = MaterialTheme.typography.bodySmall,
                fontWeight = FontWeight.Bold,
            )
        }
    }
}
