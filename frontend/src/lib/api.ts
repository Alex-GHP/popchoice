export interface MediaPayload {
  title: string;
  type: string;
  genres: string[];
  description: string;
  user_rating: number;
  gf_rating: number;
  user_review: string;
  gf_review: string;
}

export interface StartResponse {
  thread_id: string;
  question: string;
}

export interface ReplyResponse {
  done: boolean;
  question?: string;
  recommendation?: string;
}

export interface SearchResult {
  tmdb_id: number;
  title: string;
  type: string;
  year: string;
  description: string;
  genres: string[];
}

export async function searchMedia(query: string): Promise<SearchResult[]> {
  const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error("Failed to search media");
  return res.json() as Promise<SearchResult[]>;
}

export async function saveMedia(
  data: MediaPayload,
): Promise<Record<string, unknown>> {
  const res = await fetch("/api/media", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to save media");
  return res.json() as Promise<Record<string, unknown>>;
}

export async function startRecommendation(): Promise<StartResponse> {
  const res = await fetch("/api/recommend/start", { method: "POST" });
  if (!res.ok) throw new Error("Failed to start recommendation");
  return res.json() as Promise<StartResponse>;
}

export async function sendReply(
  thread_id: string,
  answer: string,
): Promise<ReplyResponse> {
  const res = await fetch("/api/recommend/reply", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ thread_id, answer }),
  });
  if (!res.ok) throw new Error("Failed to send reply");
  return res.json() as Promise<ReplyResponse>;
}
