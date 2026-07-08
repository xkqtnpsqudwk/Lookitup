import { FormEvent, useState } from "react";
import type { CreatableType, SourceCreate, SourceType } from "../types";

interface SourceFormProps {
  onAdd: (payload: SourceCreate) => Promise<void>;
  onAddPdf: (file: File, name: string) => Promise<void>;
  busy: boolean;
}

export default function SourceForm({ onAdd, onAddPdf, busy }: SourceFormProps) {
  const [name, setName] = useState("");
  const [type, setType] = useState<SourceType>("rss");
  const [url, setUrl] = useState("");
  const [content, setContent] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [fileKey, setFileKey] = useState(0);
  const [localError, setLocalError] = useState("");

  function reset() {
    setName("");
    setUrl("");
    setContent("");
    setFile(null);
    setFileKey((key) => key + 1);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLocalError("");

    try {
      if (type === "pdf") {
        if (!file) {
          setLocalError("Choose a PDF file to upload.");
          return;
        }
        await onAddPdf(file, name.trim());
        reset();
        return;
      }

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

      await onAdd({
        name: name.trim(),
        type: type as CreatableType,
        url: url.trim(),
        content: content.trim(),
      });
      reset();
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Could not add source.");
    }
  }

  return (
    <form className="sourceForm" onSubmit={handleSubmit}>
      <label>
        Source name{type === "pdf" ? " (optional)" : ""}
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
          <option value="pdf">PDF upload</option>
        </select>
      </label>

      {type === "manual" && (
        <label>
          Text content
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Paste the trusted text you want to search inside..."
            rows={4}
          />
        </label>
      )}

      {type === "pdf" && (
        <label>
          PDF file
          <input
            key={fileKey}
            type="file"
            accept="application/pdf,.pdf"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </label>
      )}

      {(type === "rss" || type === "website") && (
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
        {busy ? "Adding..." : type === "pdf" ? "Upload PDF" : "Add source"}
      </button>
    </form>
  );
}
