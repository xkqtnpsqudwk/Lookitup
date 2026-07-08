import type { SearchResult } from "../types";

interface ResultCardProps {
  result: SearchResult;
  index: number;
}

const TYPE_LABELS: Record<SearchResult["source_type"], string> = {
  rss: "RSS feed",
  website: "Website",
  manual: "Manual text",
  pdf: "PDF",
};

function formatDate(timestamp: string | null): string {
  if (!timestamp) return "No date";
  const parsed = new Date(timestamp);
  if (Number.isNaN(parsed.getTime())) return timestamp;
  return parsed.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export default function ResultCard({ result, index }: ResultCardProps) {
  return (
    <article className="resultCard">
      <div className="cardTop">
        <span className="badge trusted">Trusted Result Card {index + 1}</span>
        <span className="badge">{TYPE_LABELS[result.source_type]}</span>
        <span className={`badge recency-${result.recency.replace(" ", "-").toLowerCase()}`}>
          {result.recency}
        </span>
      </div>

      <h3>{result.title}</h3>
      <p className="cardMeta">
        {result.source_name} · {formatDate(result.timestamp)}
        {result.url && (
          <>
            {" · "}
            <a href={result.url} target="_blank" rel="noreferrer">
              Open source
            </a>
          </>
        )}
      </p>

      <blockquote>{result.excerpt}</blockquote>

      <footer className="cardFooter">
        <span>Matches: {result.match_count}</span>
        <span>Score: {result.score}</span>
        <span className="explanation">{result.explanation}</span>
      </footer>
    </article>
  );
}
