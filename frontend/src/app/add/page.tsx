"use client";

import { ArrowLeft, Plus, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { ThemeToggle } from "@/components/theme-toggle";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { type SearchResult, saveMedia, searchMedia } from "@/lib/api";

interface FormState {
  title: string;
  type: string;
  genreInput: string;
  genres: string[];
  description: string;
  user_rating: string;
  gf_rating: string;
  user_review: string;
  gf_review: string;
}

const EMPTY: FormState = {
  title: "",
  type: "movie",
  genreInput: "",
  genres: [],
  description: "",
  user_rating: "",
  gf_rating: "",
  user_review: "",
  gf_review: "",
};

export default function AddPage() {
  const [form, setForm] = useState<FormState>(EMPTY);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const genreIdCounter = useRef(0);

  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  // Prevents the useEffect from firing a new search when we just selected a result.
  const skipNextSearch = useRef(false);

  useEffect(() => {
    if (skipNextSearch.current) {
      skipNextSearch.current = false;
      return;
    }
    if (form.title.length < 2) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }
    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const results = await searchMedia(form.title);
        setSearchResults(results);
        setShowDropdown(results.length > 0);
      } catch {
        // silently ignore — the user can still fill the form manually
      } finally {
        setIsSearching(false);
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [form.title]);

  function selectResult(result: SearchResult) {
    skipNextSearch.current = true;
    setForm((f) => ({
      ...f,
      title: result.title,
      type: result.type,
      description: result.description,
      genres: result.genres.map((g) => g.toLowerCase()),
    }));
    setShowDropdown(false);
    setSearchResults([]);
  }

  function field(key: keyof FormState) {
    return (
      e: React.ChangeEvent<
        HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
      >,
    ) => setForm((f) => ({ ...f, [key]: e.target.value }));
  }

  function addGenre() {
    const g = form.genreInput.trim().toLowerCase();
    if (g && !form.genres.includes(g)) {
      setForm((f) => ({ ...f, genres: [...f.genres, g], genreInput: "" }));
    }
  }

  function removeGenre(genre: string) {
    setForm((f) => ({ ...f, genres: f.genres.filter((g) => g !== genre) }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await saveMedia({
        title: form.title,
        type: form.type,
        genres: form.genres,
        description: form.description,
        user_rating: Number(form.user_rating),
        gf_rating: Number(form.gf_rating),
        user_review: form.user_review,
        gf_review: form.gf_review,
      });
      setSuccess(true);
    } catch {
      setError("Failed to save. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-background text-foreground">
        <header className="flex items-center justify-between p-4">
          <Link
            href="/"
            className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </Link>
          <ThemeToggle />
        </header>
        <main className="flex flex-col items-center justify-center gap-6 px-4 py-24">
          <p className="text-lg font-semibold">Saved!</p>
          <div className="flex gap-3">
            <Button
              onClick={() => {
                setSuccess(false);
                setForm(EMPTY);
              }}
            >
              Add another
            </Button>
            <Link
              href="/"
              className="flex items-center rounded-md border border-border px-4 py-2 text-sm font-medium hover:bg-secondary"
            >
              Home
            </Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="flex items-center justify-between p-4">
        <Link
          href="/"
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Link>
        <ThemeToggle />
      </header>

      <main className="mx-auto max-w-lg px-4 pb-12">
        <h1 className="mb-6 text-2xl font-bold">Log Watched</h1>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          {/* Title with autocomplete */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="title">Title</Label>
            <div className="relative">
              <Input
                id="title"
                required
                value={form.title}
                onChange={field("title")}
                onBlur={() => setTimeout(() => setShowDropdown(false), 150)}
                placeholder="e.g. White Chicks"
                autoComplete="off"
              />
              {isSearching && (
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
                  Searching…
                </span>
              )}
              {showDropdown && (
                <div className="absolute z-10 mt-1 w-full overflow-hidden rounded-md border border-border bg-background shadow-md">
                  {searchResults.map((r) => (
                    <button
                      key={r.tmdb_id}
                      type="button"
                      onMouseDown={() => selectResult(r)}
                      className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-secondary"
                    >
                      <span className="font-medium">{r.title}</span>
                      {r.year && (
                        <span className="text-muted-foreground">{r.year}</span>
                      )}
                      <span className="ml-auto shrink-0 text-xs capitalize text-muted-foreground">
                        {r.type}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Type */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="type">Type</Label>
            <select
              id="type"
              value={form.type}
              onChange={field("type")}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="movie">Movie</option>
              <option value="series">Series</option>
            </select>
          </div>

          {/* Genres */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="genre-input">Genres</Label>
            <div className="flex gap-2">
              <Input
                id="genre-input"
                value={form.genreInput}
                onChange={field("genreInput")}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addGenre();
                  }
                }}
                placeholder="e.g. comedy"
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={addGenre}
                aria-label="Add genre"
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            {form.genres.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1.5">
                {form.genres.map((g) => {
                  genreIdCounter.current += 1;
                  return (
                    <Badge
                      key={`${g}-${genreIdCounter.current}`}
                      variant="outline"
                      className="gap-1"
                    >
                      {g}
                      <button
                        type="button"
                        onClick={() => removeGenre(g)}
                        aria-label={`Remove ${g}`}
                        className="hover:text-destructive"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  );
                })}
              </div>
            )}
          </div>

          {/* Description */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              required
              value={form.description}
              onChange={field("description")}
              placeholder="Brief description of the plot..."
            />
          </div>

          {/* Ratings */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="user_rating">Your Rating (1–10)</Label>
              <Input
                id="user_rating"
                type="number"
                min={1}
                max={10}
                required
                value={form.user_rating}
                onChange={field("user_rating")}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="gf_rating">Lucia's Rating (1–10)</Label>
              <Input
                id="gf_rating"
                type="number"
                min={1}
                max={10}
                required
                value={form.gf_rating}
                onChange={field("gf_rating")}
              />
            </div>
          </div>

          {/* Reviews */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="user_review">Your Review (optional)</Label>
            <Textarea
              id="user_review"
              value={form.user_review}
              onChange={field("user_review")}
              placeholder="What did you think?"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="gf_review">Lucia's Review (optional)</Label>
            <Textarea
              id="gf_review"
              value={form.gf_review}
              onChange={field("gf_review")}
              placeholder="What did she think?"
            />
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Saving..." : "Save"}
          </Button>
        </form>
      </main>
    </div>
  );
}
