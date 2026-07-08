import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

type SortBy = "BM25 relevance" | "newest first";

type SourceRecord = {
  id: string;
  source_name: string;
  source_type: string;
  source_url?: string;
  title?: string;
  timestamp?: string | null;
  trust_label?: string;
};

type TrustedResultCard = {
  chunk_id: number;
  document_id: string;
  source_name: string;
  source_type: string;
  source_format: string;
  title: string;
  matched_quote: string;
  url?: string;
  timestamp?: string | null;
  date_display: string;
  recency: "Recent" | "Older" | "No date";
  trust_label: string;
  chunk_index: number;
  score: number;
  match_count: number;
  exact_match_count: number;
  explanation: string;
};

type SearchState = {
  status: "evidence_found" | "mismatch" | "not_found";
  label: string;
  message: string;
};

type SearchResponse = {
  query: string;
  selected_sources: SourceRecord[];
  status: SearchState;
  index_stats: {
    documents: number;
    chunks: number;
  };
  cards: TrustedResultCard[];
};

type SourceListResponse = {
  count: number;
  sources: SourceRecord[];
};

type DemoScenario = {
  label: string;
  query: string;
  sourceIds: string[];
};

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const NO_RESULTS_TEXT =
  "No result found does not mean the claim is false. It only means Lookitup could not find it inside your selected trusted sources.";

const DEMO_SCENARIOS: DemoScenario[] = [
  {
    label: "Iran Israel rockets",
    query: "Iran Israel rockets",
    sourceIds: ["sample-iran-rockets-1", "sample-iran-rockets-2", "sample-iran-rockets-3"],
  },
  {
    label: "AI copyright",
    query: "AI copyright and journalism",
    sourceIds: ["sample-ai-copyright-journalism"],
  },
  {
    label: "France AI regulation",
    query: "France AI regulation",
    sourceIds: ["sample-france-ai-regulation"],
  },
  {
    label: "Fake image",
    query: "fake image on social media",
    sourceIds: ["sample-fake-image-social-media"],
  },
];

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

function dateLabel(value?: string | null) {
  return value || "No date";
}

function normalizeState(result: SearchResponse | null) {
  if (!result) return null;
  if (result.cards.length === 0) {
    return {
      tone: "empty",
      title: "No trusted result found",
      message: NO_RESULTS_TEXT,
    };
  }
  return {
    tone: "success",
    title: `${result.cards.length} trusted result${result.cards.length === 1 ? "" : "s"} found`,
    message: "Search results are limited to your selected trusted sources.",
  };
}

export default function App() {
  const [sources, setSources] = useState<SourceRecord[]>([]);
  const [selectedSourceIds, setSelectedSourceIds] = useState<string[]>([]);
  const [includeSamples, setIncludeSamples] = useState(true);
  const [query, setQuery] = useState("Iran Israel rockets");
  const [sortBy, setSortBy] = useState<SortBy>("BM25 relevance");
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const resultPanelRef = useRef<HTMLElement | null>(null);

  const selectedSourceIdSet = useMemo(() => new Set(selectedSourceIds), [selectedSourceIds]);

  const selectedSources = useMemo(
    () => sources.filter((source) => selectedSourceIdSet.has(source.id)),
    [sources, selectedSourceIdSet],
  );

  const selectedSourceTypeCounts = useMemo(() => {
    return selectedSources.reduce<Record<string, number>>((counts, source) => {
      counts[source.source_type] = (counts[source.source_type] || 0) + 1;
      return counts;
    }, {});
  }, [selectedSources]);

  const resultState = normalizeState(searchResult);

  useEffect(() => {
    fetchJson<SourceListResponse>(`/sources?include_samples=${includeSamples}`)
      .then((data) => {
        setSources(data.sources);
        setSelectedSourceIds((current) => {
          const availableIds = new Set(data.sources.map((source) => source.id));
          const keptIds = current.filter((sourceId) => availableIds.has(sourceId));
          return keptIds.length ? keptIds : data.sources.map((source) => source.id);
        });
      })
      .catch(() => {
        setError("Backend is not reachable. Start FastAPI on http://127.0.0.1:8000.");
      });
    setSearchResult(null);
  }, [includeSamples]);

  useEffect(() => {
    if (!searchResult) return;
    window.setTimeout(() => {
      resultPanelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 80);
  }, [searchResult]);

  async function runSearch(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    if (!query.trim()) {
      setError("Enter a topic, keyword, event, or claim first.");
      return;
    }
    if (selectedSourceIds.length === 0) {
      setError("Select at least one trusted source first.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const result = await fetchJson<SearchResponse>("/search", {
        method: "POST",
        body: JSON.stringify({
          query,
          source_ids: selectedSourceIds,
          include_samples: includeSamples,
          sort_by: sortBy,
          limit: 12,
        }),
      });
      setSearchResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed.");
    } finally {
      setLoading(false);
    }
  }

  function toggleSource(sourceId: string) {
    setSelectedSourceIds((current) =>
      current.includes(sourceId)
        ? current.filter((selectedId) => selectedId !== sourceId)
        : [...current, sourceId],
    );
    setSearchResult(null);
  }

  function selectAllSources() {
    setSelectedSourceIds(sources.map((source) => source.id));
    setSearchResult(null);
  }

  function clearSourceSelection() {
    setSelectedSourceIds([]);
    setSearchResult(null);
  }

  function applyDemoScenario(scenario: DemoScenario) {
    setIncludeSamples(true);
    setSelectedSourceIds(scenario.sourceIds);
    setQuery(scenario.query);
    setSearchResult(null);
  }

  return (
    <main>
      <header className="hero">
        <p className="eyebrow">Trusted-source search for journalists</p>
        <div className="heroRow">
          <div>
            <h1>Lookitup</h1>
            <p className="subtitle">Having a doubt? Just Lookitup.</p>
          </div>
          <a className="apiLink" href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">
            API Docs
          </a>
        </div>
        <p className="heroCopy">
          Google searches the open web. Lookitup searches your trusted world. Select sources,
          search a topic, then review the Trusted Result Cards.
        </p>
      </header>

      {error && <div className="alert danger">{error}</div>}

      <section className="stepGrid">
        <section className="panel stepPanel">
          <div className="stepHeader">
            <span>1</span>
            <div>
              <p className="eyebrow">Source selection</p>
              <h2>Select trusted sources</h2>
            </div>
          </div>

          <div className="sourceToolbar">
            <label className="checkRow">
              <input
                type="checkbox"
                checked={includeSamples}
                onChange={(event) => setIncludeSamples(event.target.checked)}
              />
              Show demo sample sources
            </label>
            <div>
              <button type="button" onClick={selectAllSources} disabled={sources.length === 0}>
                Select all
              </button>
              <button type="button" onClick={clearSourceSelection} disabled={selectedSourceIds.length === 0}>
                Clear
              </button>
            </div>
          </div>

          <div className="sourceSummary">
            <div>
              <small>Selected sources</small>
              <strong>{selectedSourceIds.length}</strong>
            </div>
            <div>
              <small>Available sources</small>
              <strong>{sources.length}</strong>
            </div>
            <div>
              <small>Selected formats</small>
              <strong>{Object.keys(selectedSourceTypeCounts).length}</strong>
            </div>
          </div>

          <div className="sourceList">
            {sources.length === 0 ? (
              <p className="muted">No trusted sources are available yet.</p>
            ) : (
              sources.map((source) => {
                const selected = selectedSourceIdSet.has(source.id);
                return (
                  <label className={selected ? "sourceCard active" : "sourceCard"} key={source.id}>
                    <input
                      type="checkbox"
                      checked={selected}
                      onChange={() => toggleSource(source.id)}
                    />
                    <span className="sourceCardBody">
                      <strong>{source.source_name}</strong>
                      <span className="sourceMeta">
                        {source.source_type} - {dateLabel(source.timestamp)}
                      </span>
                      <span className="trustLabel">{source.trust_label || "Trusted source"}</span>
                    </span>
                  </label>
                );
              })
            )}
          </div>
        </section>

        <section className="panel stepPanel">
          <div className="stepHeader">
            <span>2</span>
            <div>
              <p className="eyebrow">Topic search</p>
              <h2>Search inside selected sources</h2>
            </div>
          </div>

          <form className="searchForm" onSubmit={runSearch}>
            <label>
              Topic, keyword, event, or claim
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Iran Israel rockets"
              />
            </label>

            <div className="searchControls">
              <label>
                Sort results
                <select value={sortBy} onChange={(event) => setSortBy(event.target.value as SortBy)}>
                  <option value="BM25 relevance">Relevance</option>
                  <option value="newest first">Newest first</option>
                </select>
              </label>
              <button type="submit" disabled={loading || selectedSourceIds.length === 0}>
                {loading ? "Searching..." : "Search selected sources"}
              </button>
            </div>
          </form>

          <div className="demoQueries">
            <span>Demo queries</span>
            {DEMO_SCENARIOS.map((scenario) => (
              <button
                key={scenario.label}
                type="button"
                onClick={() => applyDemoScenario(scenario)}
              >
                {scenario.label}
              </button>
            ))}
          </div>

          <p className="hint">
            Search is keyword-based and fast. The backend only searches the sources checked in step 1.
          </p>
        </section>
      </section>

      <section className="panel resultPanel" ref={resultPanelRef}>
        <div className="stepHeader resultHeader">
          <span>3</span>
          <div>
            <p className="eyebrow">Result review</p>
            <h2>Check Trusted Result Cards</h2>
          </div>
          {searchResult && (
            <div className="resultStats">
              <strong>{searchResult.cards.length}</strong>
              <span>results</span>
              <strong>{searchResult.index_stats.documents}</strong>
              <span>sources</span>
              <strong>{searchResult.index_stats.chunks}</strong>
              <span>chunks</span>
            </div>
          )}
        </div>

        {!searchResult && (
          <div className="emptyState">
            <strong>Run a search to review trusted results.</strong>
            <p>Recommended demo: click Iran Israel rockets, then search selected sources.</p>
          </div>
        )}

        {searchResult && resultState && (
          <>
            <div className={`resultBanner ${resultState.tone}`}>
              <strong>{resultState.title}</strong>
              <span>{resultState.message}</span>
            </div>

            <div className="cards">
              {searchResult.cards.map((card, index) => (
                <article className="trustedCard" key={`${card.document_id}-${card.chunk_id}`}>
                  <div className="cardTopline">
                    <span className="trustedBadge">Trusted Result Card {index + 1}</span>
                    <span>{card.source_format}</span>
                    <span>{card.recency}</span>
                  </div>
                  <h3>{card.title}</h3>
                  <p className="meta">
                    {card.source_name} - {card.date_display}
                    {card.url && (
                      <>
                        {" "}
                        - <a href={card.url} target="_blank" rel="noreferrer">Open source</a>
                      </>
                    )}
                  </p>
                  <blockquote>{card.matched_quote}</blockquote>
                  <footer>
                    <span>Matches: {card.match_count}</span>
                    <span>Exact phrase: {card.exact_match_count}</span>
                    <span>Score: {card.score}</span>
                  </footer>
                  <p className="explanation">{card.explanation}</p>
                </article>
              ))}
            </div>
          </>
        )}
      </section>
    </main>
  );
}
