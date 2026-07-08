import { useEffect, useState } from "react";
import { api } from "../api/client";
import ResultCard from "../components/ResultCard";
import SearchBar from "../components/SearchBar";
import SourceForm from "../components/SourceForm";
import SourceList from "../components/SourceList";
import type { SearchResponse, SortOption, Source, SourceCreate } from "../types";

const NO_RESULTS_TEXT =
  "No result found does not mean the claim is false. It only means Lookitup could not find it inside your selected trusted sources.";

const NO_SOURCES_TEXT =
  "Add trusted sources first. Lookitup only searches inside sources you choose.";

export default function HomePage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [sourceBusy, setSourceBusy] = useState(false);
  const [query, setQuery] = useState("Iran Israel rockets");
  const [sort, setSort] = useState<SortOption>("relevance");
  const [searchBusy, setSearchBusy] = useState(false);
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [error, setError] = useState("");

  async function refreshSources() {
    try {
      setSources(await api.getSources());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load sources.");
    }
  }

  useEffect(() => {
    refreshSources();
  }, []);

  async function handleAddSource(payload: SourceCreate) {
    setSourceBusy(true);
    setError("");
    try {
      await api.addSource(payload);
      await refreshSources();
    } finally {
      setSourceBusy(false);
    }
  }

  async function handleLoadSamples() {
    setSourceBusy(true);
    setError("");
    try {
      await api.loadSamples();
      await refreshSources();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load samples.");
    } finally {
      setSourceBusy(false);
    }
  }

  async function handleClearSources() {
    setSourceBusy(true);
    setError("");
    try {
      await api.clearSources();
      setResult(null);
      await refreshSources();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not clear sources.");
    } finally {
      setSourceBusy(false);
    }
  }

  async function handleSearch() {
    if (!query.trim()) {
      setError("Enter a keyword or claim to search.");
      return;
    }
    if (sources.length === 0) {
      setError(NO_SOURCES_TEXT);
      return;
    }
    setSearchBusy(true);
    setError("");
    try {
      setResult(await api.search(query, sort));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed.");
    } finally {
      setSearchBusy(false);
    }
  }

  return (
    <>
      {error && <div className="alert danger">{error}</div>}

      <section className="stepGrid">
        <section className="panel">
          <div className="stepHeader">
            <span>1</span>
            <div>
              <p className="eyebrow">Source setup</p>
              <h2>Add trusted sources</h2>
            </div>
          </div>

          <SourceForm onAdd={handleAddSource} busy={sourceBusy} />

          <div className="sourceActions">
            <button type="button" onClick={handleLoadSamples} disabled={sourceBusy}>
              Load sample sources
            </button>
            <button
              type="button"
              className="ghostDanger"
              onClick={handleClearSources}
              disabled={sourceBusy || sources.length === 0}
            >
              Clear all sources
            </button>
          </div>

          <div className="sourceListHead">
            <p className="eyebrow">Current sources</p>
            <span className="countPill">{sources.length}</span>
          </div>
          <SourceList sources={sources} />
        </section>

        <section className="panel">
          <div className="stepHeader">
            <span>2</span>
            <div>
              <p className="eyebrow">Trusted search</p>
              <h2>Search inside your sources</h2>
            </div>
          </div>

          <SearchBar
            query={query}
            sort={sort}
            busy={searchBusy}
            disabled={sources.length === 0}
            onQueryChange={setQuery}
            onSortChange={setSort}
            onSubmit={handleSearch}
          />

          <p className="hint">
            Search is keyword-based and stays inside your trusted sources. It never queries
            the open web.
          </p>

          {sources.length === 0 && (
            <div className="emptyState small">
              <strong>No trusted sources yet.</strong>
              <p>{NO_SOURCES_TEXT}</p>
            </div>
          )}
        </section>
      </section>

      <section className="panel resultPanel">
        <div className="stepHeader">
          <span>3</span>
          <div>
            <p className="eyebrow">Trusted results</p>
            <h2>Trusted Result Cards</h2>
          </div>
          {result && (
            <span className="countPill big">
              {result.count} result{result.count === 1 ? "" : "s"}
            </span>
          )}
        </div>

        {!result && (
          <div className="emptyState">
            <strong>Run a search to review trusted results.</strong>
            <p>Try loading the sample sources, then search "Iran Israel rockets".</p>
          </div>
        )}

        {result && result.results.length === 0 && (
          <div className="resultBanner empty">
            <strong>No trusted result found</strong>
            <span>{NO_RESULTS_TEXT}</span>
          </div>
        )}

        {result && result.results.length > 0 && (
          <div className="cards">
            {result.results.map((item, index) => (
              <ResultCard key={item.id} result={item} index={index} />
            ))}
          </div>
        )}
      </section>
    </>
  );
}
