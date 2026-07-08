import { FormEvent, useEffect, useMemo, useState } from "react";

type SortBy = "BM25 relevance" | "newest first";
type SummaryStyle = "short paragraph" | "bullet points" | "timeline";
type SourceFormType = "Local sample text" | "URL" | "RSS";

type SourcePack = {
  id: string;
  name: string;
  description: string;
  created_by?: string;
  created_at?: string;
};

type SourceRecord = {
  id: string;
  source_name: string;
  source_type: string;
  source_url?: string;
  title?: string;
  timestamp?: string | null;
  trust_label?: string;
  pack_id?: string;
};

type EvidenceCard = {
  chunk_id: number;
  document_id: string;
  source_name: string;
  source_type: string;
  title: string;
  matched_quote: string;
  url?: string;
  timestamp?: string | null;
  date_display: string;
  trust_label: string;
  chunk_index: number;
  score: number;
  match_count: number;
};

type SearchState = {
  status: "evidence_found" | "mismatch" | "not_found";
  label: string;
  message: string;
};

type IndexStats = {
  documents: number;
  chunks: number;
};

type SearchResponse = {
  query: string;
  source_pack: SourcePack;
  status: SearchState;
  index_stats: IndexStats;
  cards: EvidenceCard[];
};

type EvidenceGroup = {
  source_name: string;
  date: string;
  count: number;
  top_score: number;
  cards: EvidenceCard[];
};

type GroupResponse = SearchResponse & {
  grouping_message: string;
  groups: EvidenceGroup[];
};

type SummaryResponse = SearchResponse & {
  summary: {
    mode: string;
    summary: string;
    notice: string;
  };
};

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

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

function stateClass(status?: SearchState["status"]) {
  if (status === "evidence_found") return "stateBanner success";
  if (status === "mismatch") return "stateBanner warning";
  if (status === "not_found") return "stateBanner danger";
  return "stateBanner";
}

function formatDate(value?: string | null) {
  return value || "No date";
}

export default function App() {
  const [packs, setPacks] = useState<SourcePack[]>([]);
  const [selectedPackId, setSelectedPackId] = useState("international-breaking-news");
  const [sources, setSources] = useState<SourceRecord[]>([]);
  const [includeSamples, setIncludeSamples] = useState(true);
  const [claim, setClaim] = useState("Iran Israel rockets");
  const [sortBy, setSortBy] = useState<SortBy>("BM25 relevance");
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null);
  const [groupResult, setGroupResult] = useState<GroupResponse | null>(null);
  const [summaryStyle, setSummaryStyle] = useState<SummaryStyle>("bullet points");
  const [summaryResult, setSummaryResult] = useState<SummaryResponse | null>(null);
  const [sourceType, setSourceType] = useState<SourceFormType>("Local sample text");
  const [sourceName, setSourceName] = useState("");
  const [trustLabel, setTrustLabel] = useState("Trusted source");
  const [sourceUrl, setSourceUrl] = useState("");
  const [sourceTitle, setSourceTitle] = useState("");
  const [sourceText, setSourceText] = useState("");
  const [sourceTimestamp, setSourceTimestamp] = useState("");
  const [rssLimit, setRssLimit] = useState(8);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const selectedPack = useMemo(
    () => packs.find((pack) => pack.id === selectedPackId),
    [packs, selectedPackId],
  );

  const sourceTypeCounts = useMemo(() => {
    return sources.reduce<Record<string, number>>((counts, source) => {
      counts[source.source_type] = (counts[source.source_type] || 0) + 1;
      return counts;
    }, {});
  }, [sources]);

  useEffect(() => {
    fetchJson<SourcePack[]>("/source-packs")
      .then((data) => {
        setPacks(data);
        if (data.length && !data.some((pack) => pack.id === selectedPackId)) {
          setSelectedPackId(data[0].id);
        }
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!selectedPackId) return;
    fetchJson<{ count: number; sources: SourceRecord[] }>(
      `/sources?pack_id=${encodeURIComponent(selectedPackId)}&include_samples=${includeSamples}`,
    )
      .then((data) => setSources(data.sources))
      .catch((err: Error) => setError(err.message));
  }, [selectedPackId, includeSamples]);

  async function runSearch() {
    if (!claim.trim()) {
      setError("Enter a claim or keyword first.");
      return;
    }
    setLoading(true);
    setError("");
    setNotice("");
    setSummaryResult(null);
    try {
      const payload = {
        query: claim,
        source_pack_id: selectedPackId,
        include_samples: includeSamples,
        sort_by: sortBy,
        limit: 12,
      };
      const result = await fetchJson<SearchResponse>("/search", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setSearchResult(result);
      setGroupResult(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed.");
    } finally {
      setLoading(false);
    }
  }

  async function runGroupedEvidence() {
    setLoading(true);
    setError("");
    try {
      const result = await fetchJson<GroupResponse>("/evidence/group", {
        method: "POST",
        body: JSON.stringify({
          query: claim,
          source_pack_id: selectedPackId,
          include_samples: includeSamples,
          sort_by: sortBy,
          limit: 12,
        }),
      });
      setSearchResult(result);
      setGroupResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Grouping failed.");
    } finally {
      setLoading(false);
    }
  }

  async function runSummary() {
    setLoading(true);
    setError("");
    try {
      const result = await fetchJson<SummaryResponse>("/evidence/summary", {
        method: "POST",
        body: JSON.stringify({
          query: claim,
          source_pack_id: selectedPackId,
          include_samples: includeSamples,
          sort_by: sortBy,
          limit: 12,
          style: summaryStyle,
        }),
      });
      setSearchResult(result);
      setSummaryResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Summary failed.");
    } finally {
      setLoading(false);
    }
  }

  async function addSource(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setNotice("");
    try {
      let path = "/sources/local";
      let body: Record<string, unknown> = {
        pack_id: selectedPackId,
        source_name: sourceName,
        trust_label: trustLabel,
      };

      if (sourceType === "URL") {
        path = "/sources/url";
        body = { ...body, url: sourceUrl };
      } else if (sourceType === "RSS") {
        path = "/sources/rss";
        body = { ...body, url: sourceUrl, limit: rssLimit };
      } else {
        body = {
          ...body,
          title: sourceTitle,
          text: sourceText,
          url: sourceUrl,
          timestamp: sourceTimestamp || null,
        };
      }

      await fetchJson(path, {
        method: "POST",
        body: JSON.stringify(body),
      });
      const refreshed = await fetchJson<{ count: number; sources: SourceRecord[] }>(
        `/sources?pack_id=${encodeURIComponent(selectedPackId)}&include_samples=${includeSamples}`,
      );
      setSources(refreshed.sources);
      setNotice("Source added to the selected pack.");
      setSourceName("");
      setSourceUrl("");
      setSourceTitle("");
      setSourceText("");
      setSourceTimestamp("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add source.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <header className="hero">
        <div>
          <p className="eyebrow">Controlled retrieval before publication</p>
          <h1>Lookitup</h1>
          <p className="subtitle">
            Google searches the open web. Lookitup searches your trusted world.
          </p>
        </div>
        <div className="heroActions">
          <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">
            API Docs
          </a>
        </div>
      </header>

      <section className="workflow">
        <div>
          <span>1</span>
          <strong>Select source pack</strong>
        </div>
        <div>
          <span>2</span>
          <strong>Search a claim</strong>
        </div>
        <div>
          <span>3</span>
          <strong>Review Evidence Cards</strong>
        </div>
      </section>

      {error && <div className="alert danger">{error}</div>}
      {notice && <div className="alert success">{notice}</div>}

      <section className="layout">
        <aside className="panel sidebar">
          <div className="panelHeader">
            <p className="eyebrow">Source pack</p>
            <h2>Trusted Corpus</h2>
          </div>

          <label>
            Pack
            <select value={selectedPackId} onChange={(event) => setSelectedPackId(event.target.value)}>
              {packs.map((pack) => (
                <option key={pack.id} value={pack.id}>
                  {pack.name}
                </option>
              ))}
            </select>
          </label>

          <p className="muted">{selectedPack?.description || "No source pack selected."}</p>

          <label className="checkRow">
            <input
              type="checkbox"
              checked={includeSamples}
              onChange={(event) => setIncludeSamples(event.target.checked)}
            />
            Include local sample fallback
          </label>

          <div className="stats">
            <div>
              <small>Documents</small>
              <strong>{sources.length}</strong>
            </div>
            <div>
              <small>Types</small>
              <strong>{Object.keys(sourceTypeCounts).length}</strong>
            </div>
          </div>

          <div className="typeList">
            {Object.entries(sourceTypeCounts).map(([type, count]) => (
              <span key={type}>
                {type}: {count}
              </span>
            ))}
          </div>

          <form className="sourceForm" onSubmit={addSource}>
            <h3>Add source</h3>
            <label>
              Source type
              <select value={sourceType} onChange={(event) => setSourceType(event.target.value as SourceFormType)}>
                <option>Local sample text</option>
                <option>URL</option>
                <option>RSS</option>
              </select>
            </label>
            <label>
              Source name
              <input value={sourceName} onChange={(event) => setSourceName(event.target.value)} placeholder="Trusted source name" />
            </label>
            <label>
              Trust label
              <input value={trustLabel} onChange={(event) => setTrustLabel(event.target.value)} />
            </label>

            {(sourceType === "URL" || sourceType === "RSS") && (
              <label>
                URL
                <input value={sourceUrl} onChange={(event) => setSourceUrl(event.target.value)} placeholder="https://example.com" />
              </label>
            )}

            {sourceType === "RSS" && (
              <label>
                RSS entries
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={rssLimit}
                  onChange={(event) => setRssLimit(Number(event.target.value))}
                />
              </label>
            )}

            {sourceType === "Local sample text" && (
              <>
                <label>
                  Title
                  <input value={sourceTitle} onChange={(event) => setSourceTitle(event.target.value)} />
                </label>
                <label>
                  Optional URL
                  <input value={sourceUrl} onChange={(event) => setSourceUrl(event.target.value)} />
                </label>
                <label>
                  Optional timestamp
                  <input value={sourceTimestamp} onChange={(event) => setSourceTimestamp(event.target.value)} placeholder="2026-06-18T09:30:00Z" />
                </label>
                <label>
                  Text
                  <textarea value={sourceText} onChange={(event) => setSourceText(event.target.value)} rows={5} />
                </label>
              </>
            )}
            <button type="submit" disabled={loading}>
              Add to pack
            </button>
          </form>
        </aside>

        <section className="content">
          <section className="panel searchPanel">
            <div className="panelHeader">
              <p className="eyebrow">Claim search</p>
              <h2>Search only trusted sources</h2>
            </div>
            <label>
              Text claim or keyword query
              <textarea value={claim} onChange={(event) => setClaim(event.target.value)} rows={3} />
            </label>
            <div className="toolbar">
              <label>
                Sort
                <select value={sortBy} onChange={(event) => setSortBy(event.target.value as SortBy)}>
                  <option>BM25 relevance</option>
                  <option>newest first</option>
                </select>
              </label>
              <button onClick={runSearch} disabled={loading}>
                Search
              </button>
              <button className="secondary" onClick={runGroupedEvidence} disabled={loading}>
                Group evidence
              </button>
              <button className="secondary" onClick={runSummary} disabled={loading}>
                Summarize
              </button>
            </div>
          </section>

          <section className="panel resultPanel">
            <div className="panelHeader rowHeader">
              <div>
                <p className="eyebrow">Evidence review</p>
                <h2>Evidence Cards</h2>
              </div>
              {searchResult && (
                <div className="compactStats">
                  <span>{searchResult.cards.length} cards</span>
                  <span>{searchResult.index_stats.documents} docs</span>
                  <span>{searchResult.index_stats.chunks} chunks</span>
                </div>
              )}
            </div>

            {!searchResult && (
              <div className="emptyState">
                <strong>Run a search to retrieve Evidence Cards.</strong>
                <p>Try the demo query: Iran Israel rockets</p>
              </div>
            )}

            {searchResult && (
              <>
                <div className={stateClass(searchResult.status.status)}>
                  <strong>{searchResult.status.label}</strong>
                  <span>{searchResult.status.message}</span>
                </div>

                {groupResult && (
                  <div className="groups">
                    <h3>Evidence grouped by source and time</h3>
                    {groupResult.groups.map((group) => (
                      <div className="groupCard" key={`${group.source_name}-${group.date}`}>
                        <strong>{group.source_name}</strong>
                        <span>{group.date}</span>
                        <span>{group.count} card(s)</span>
                      </div>
                    ))}
                  </div>
                )}

                {summaryResult && (
                  <div className="summaryBox">
                    <div className="summaryHeader">
                      <strong>{summaryResult.summary.mode}</strong>
                      <label>
                        Format
                        <select value={summaryStyle} onChange={(event) => setSummaryStyle(event.target.value as SummaryStyle)}>
                          <option>short paragraph</option>
                          <option>bullet points</option>
                          <option>timeline</option>
                        </select>
                      </label>
                    </div>
                    <pre>{summaryResult.summary.summary}</pre>
                    <small>{summaryResult.summary.notice}</small>
                  </div>
                )}

                <div className="cards">
                  {searchResult.cards.map((card, index) => (
                    <article className="evidenceCard" key={`${card.document_id}-${card.chunk_id}`}>
                      <div className="cardBadges">
                        <span>Evidence Card {index + 1}</span>
                        <span>{card.source_type}</span>
                        <span>{card.trust_label}</span>
                      </div>
                      <h3>{card.title}</h3>
                      <p className="meta">
                        {card.source_name} · {formatDate(card.date_display)}
                        {card.url && (
                          <>
                            {" "}
                            · <a href={card.url} target="_blank" rel="noreferrer">Open source</a>
                          </>
                        )}
                      </p>
                      <blockquote>{card.matched_quote}</blockquote>
                      <footer>
                        Score {card.score} · Hits {card.match_count} · Chunk #{card.chunk_index}
                      </footer>
                    </article>
                  ))}
                </div>
              </>
            )}
          </section>
        </section>
      </section>
    </main>
  );
}
