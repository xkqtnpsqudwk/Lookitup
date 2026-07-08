import type { Source } from "../types";

interface SourceListProps {
  sources: Source[];
}

const TYPE_LABELS: Record<Source["type"], string> = {
  rss: "RSS feed",
  website: "Website",
  manual: "Manual text",
};

export default function SourceList({ sources }: SourceListProps) {
  if (sources.length === 0) {
    return (
      <div className="emptyState small">
        <strong>No trusted sources yet.</strong>
        <p>Add trusted sources first. Lookitup only searches inside sources you choose.</p>
      </div>
    );
  }

  return (
    <ul className="sourceList">
      {sources.map((source) => (
        <li className="sourceRow" key={source.id}>
          <div className="sourceRowMain">
            <strong>{source.name}</strong>
            <span className="sourceMeta">
              {TYPE_LABELS[source.type]} · {source.item_count} item
              {source.item_count === 1 ? "" : "s"}
            </span>
          </div>
          {source.url && (
            <a href={source.url} target="_blank" rel="noreferrer" className="sourceLink">
              link
            </a>
          )}
        </li>
      ))}
    </ul>
  );
}
