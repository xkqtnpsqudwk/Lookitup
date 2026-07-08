import { FormEvent, useState } from "react";
import type { SourceCreate, SourceType } from "../types";

interface SourceFormProps {
  onAdd: (payload: SourceCreate) => Promise<void>;
  busy: boolean;
}

export default function SourceForm({ onAdd, busy }: SourceFormProps) {
  const [name, setName] = useState("");
  const [type, setType] = useState<SourceType>("rss");
  const [url, setUrl] = useState("");
  const [content, setContent] = useState("");
  const [localError, setLocalError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLocalError("");

    if (!name.trim() && type === "manual") {
      setLocalError("Give the manual source a name.");
      return;
    }
    if ((type === "rss" || type === "website") && !url.trim()) {
      setLocalError("Enter a URL for an RSS or website source.");
      return;
    }
    if (type === "manual" && !content.trim()) {
      setLocalError("Manual text cannot be empty.");
      return;
    }

    try {
      await onAdd({
        name: name.trim(),
        type,
        url: url.trim(),
        content: content.trim(),
      });
      setName("");
      setUrl("");
      setContent("");
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Could not add source.");
    }
  }

  return (
    <form className="sourceForm" onSubmit={handleSubmit}>
      <label>
        Source name
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={type === "manual" ? "Reporter's note" : "BBC RSS"}
        />
      </label>

      <label>
        Source type
        <select value={type} onChange={(e) => setType(e.target.value as SourceType)}>
          <option value="rss">RSS feed</option>
          <option value="website">Website</option>
          <option value="manual">Manual text</option>
        </select>
      </label>

      {type === "manual" ? (
        <label>
          Text content
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Paste the trusted text you want to search inside..."
            rows={4}
          />
        </label>
      ) : (
        <label>
          {type === "rss" ? "RSS feed URL" : "Website URL"}
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/rss"
          />
        </label>
      )}

      {localError && <p className="formError">{localError}</p>}

      <button type="submit" className="primaryBtn" disabled={busy}>
        {busy ? "Adding..." : "Add source"}
      </button>
    </form>
  );
}
