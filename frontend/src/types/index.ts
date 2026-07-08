export type SourceType = "rss" | "website" | "manual" | "pdf";

// PDF sources are created via file upload, not the JSON create form.
export type CreatableType = "rss" | "website" | "manual";

export type SortOption = "relevance" | "newest";

export interface Source {
  id: string;
  name: string;
  type: SourceType;
  url: string;
  created_at: string;
  item_count: number;
}

export interface SourceCreate {
  name: string;
  type: CreatableType;
  url?: string;
  content?: string;
}

export interface SearchResult {
  id: string;
  source_id: string;
  source_name: string;
  source_type: SourceType;
  title: string;
  url: string;
  timestamp: string | null;
  excerpt: string;
  match_count: number;
  score: number;
  recency: "Recent" | "Older" | "No date";
  explanation: string;
}

export interface SearchResponse {
  query: string;
  count: number;
  results: SearchResult[];
}
