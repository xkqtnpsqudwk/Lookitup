import { FormEvent } from "react";
import type { SortOption } from "../types";

interface SearchBarProps {
  query: string;
  sort: SortOption;
  busy: boolean;
  disabled: boolean;
  onQueryChange: (value: string) => void;
  onSortChange: (value: SortOption) => void;
  onSubmit: () => void;
}

export default function SearchBar({
  query,
  sort,
  busy,
  disabled,
  onQueryChange,
  onSortChange,
  onSubmit,
}: SearchBarProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }

  return (
    <form className="searchBar" onSubmit={handleSubmit}>
      <input
        className="searchInput"
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
        placeholder="Search your trusted sources, e.g. Iran Israel rockets"
        aria-label="Search query"
      />
      <select
        className="sortSelect"
        value={sort}
        onChange={(e) => onSortChange(e.target.value as SortOption)}
        aria-label="Sort results"
      >
        <option value="relevance">Relevance</option>
        <option value="newest">Newest</option>
      </select>
      <button type="submit" className="primaryBtn" disabled={busy || disabled}>
        {busy ? "Searching..." : "Search"}
      </button>
    </form>
  );
}
