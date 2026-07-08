import type { SummaryResponse, SummaryStyle } from "../types";

interface SummaryPanelProps {
  summary: SummaryResponse | null;
  busy: boolean;
  error: string;
  style: SummaryStyle;
  onStyleChange: (style: SummaryStyle) => void;
  onGenerate: () => void;
}

export default function SummaryPanel({
  summary,
  busy,
  error,
  style,
  onStyleChange,
  onGenerate,
}: SummaryPanelProps) {
  return (
    <div className="summaryBox">
      <div className="summaryHead">
        <div>
          <p className="eyebrow">AI summary (optional)</p>
          <span className="summaryNote">
            Generated only from the trusted results above — never the open web.
          </span>
        </div>
        <div className="summaryControls">
          <select
            value={style}
            onChange={(e) => onStyleChange(e.target.value as SummaryStyle)}
            aria-label="Summary style"
          >
            <option value="paragraph">Paragraph</option>
            <option value="bullets">Bullet points</option>
          </select>
          <button type="button" className="primaryBtn" onClick={onGenerate} disabled={busy}>
            {busy ? "Summarizing..." : summary ? "Regenerate" : "Generate AI summary"}
          </button>
        </div>
      </div>

      {error && <p className="summaryError">{error}</p>}

      {summary && !error && (
        <div className="summaryBody">
          {summary.style === "bullets" ? (
            <ul>
              {summary.summary
                .split("\n")
                .map((line) => line.replace(/^-\s*/, "").trim())
                .filter(Boolean)
                .map((line, i) => (
                  <li key={i}>{line}</li>
                ))}
            </ul>
          ) : (
            <p>{summary.summary}</p>
          )}
          <p className="summaryMeta">
            Based on {summary.based_on} of {summary.grounded_in} trusted result
            {summary.grounded_in === 1 ? "" : "s"} · sources: {summary.used_sources.join(", ")} ·{" "}
            {summary.model}
          </p>
        </div>
      )}
    </div>
  );
}
