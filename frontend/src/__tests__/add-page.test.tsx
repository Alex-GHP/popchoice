import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import AddPage from "@/app/add/page";
import { saveMedia, searchMedia } from "@/lib/api";

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));

vi.mock("@/components/theme-toggle", () => ({
  ThemeToggle: () => <button type="button">Toggle theme</button>,
}));

vi.mock("lucide-react", () => ({
  ArrowLeft: () => <span />,
  Plus: () => <span />,
  X: () => <span />,
}));

vi.mock("@/lib/api", () => ({
  saveMedia: vi.fn(),
  searchMedia: vi.fn(),
}));

const WHITE_CHICKS: import("@/lib/api").SearchResult = {
  tmdb_id: 8191,
  title: "White Chicks",
  type: "movie",
  year: "2004",
  description: "Two FBI agents go undercover as white women.",
  genres: ["Comedy", "Action"],
};

describe("Add page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(saveMedia).mockResolvedValue({});
    vi.mocked(searchMedia).mockResolvedValue([]);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders the form with all required fields", () => {
    render(<AddPage />);
    expect(screen.getByLabelText("Title")).toBeInTheDocument();
    expect(screen.getByLabelText("Type")).toBeInTheDocument();
    expect(screen.getByLabelText(/your rating/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/lucia's rating/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
  });

  it("can add a genre by pressing Enter", async () => {
    render(<AddPage />);
    const genreInput = screen.getByPlaceholderText("e.g. comedy");
    fireEvent.change(genreInput, { target: { value: "comedy" } });
    fireEvent.keyDown(genreInput, { key: "Enter" });
    expect(await screen.findByText("comedy")).toBeInTheDocument();
  });

  it("does not add a duplicate genre", async () => {
    render(<AddPage />);
    const genreInput = screen.getByPlaceholderText("e.g. comedy");
    fireEvent.change(genreInput, { target: { value: "drama" } });
    fireEvent.keyDown(genreInput, { key: "Enter" });
    fireEvent.change(genreInput, { target: { value: "drama" } });
    fireEvent.keyDown(genreInput, { key: "Enter" });
    const badges = await screen.findAllByText("drama");
    expect(badges).toHaveLength(1);
  });

  it("calls saveMedia with correct data on submit", async () => {
    render(<AddPage />);
    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "Parasite" },
    });
    fireEvent.change(screen.getByLabelText(/description/i), {
      target: { value: "A Korean thriller." },
    });
    fireEvent.change(screen.getByLabelText(/your rating/i), {
      target: { value: "10" },
    });
    fireEvent.change(screen.getByLabelText(/lucia's rating/i), {
      target: { value: "9" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save/i }));
    await waitFor(() => {
      expect(saveMedia).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Parasite",
          description: "A Korean thriller.",
          user_rating: 10,
          gf_rating: 9,
        }),
      );
    });
  });

  it("shows success state after successful save", async () => {
    render(<AddPage />);
    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "Parasite" },
    });
    fireEvent.change(screen.getByLabelText(/description/i), {
      target: { value: "A Korean thriller." },
    });
    fireEvent.change(screen.getByLabelText(/your rating/i), {
      target: { value: "10" },
    });
    fireEvent.change(screen.getByLabelText(/lucia's rating/i), {
      target: { value: "9" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save/i }));
    await waitFor(() => {
      expect(screen.getByText("Saved!")).toBeInTheDocument();
    });
  });

  it("shows error when saveMedia fails", async () => {
    vi.mocked(saveMedia).mockRejectedValue(new Error("Network error"));
    render(<AddPage />);
    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "Parasite" },
    });
    fireEvent.change(screen.getByLabelText(/description/i), {
      target: { value: "A Korean thriller." },
    });
    fireEvent.change(screen.getByLabelText(/your rating/i), {
      target: { value: "10" },
    });
    fireEvent.change(screen.getByLabelText(/lucia's rating/i), {
      target: { value: "9" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save/i }));
    await waitFor(() => {
      expect(screen.getByText(/failed to save/i)).toBeInTheDocument();
    });
  });

  // --- Autocomplete tests ---

  it("shows a dropdown when title search returns results", async () => {
    vi.mocked(searchMedia).mockResolvedValue([WHITE_CHICKS]);
    render(<AddPage />);
    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "White" },
    });
    expect(await screen.findByText("White Chicks")).toBeInTheDocument();
    expect(screen.getByText("2004")).toBeInTheDocument();
  });

  it("does not search when title is shorter than 2 characters", async () => {
    render(<AddPage />);
    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "W" },
    });
    // Give the debounce time to fire if it were going to.
    await new Promise((r) => setTimeout(r, 500));
    expect(searchMedia).not.toHaveBeenCalled();
  });

  it("fills title, type, description and genres when a result is selected", async () => {
    vi.mocked(searchMedia).mockResolvedValue([WHITE_CHICKS]);
    render(<AddPage />);
    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "White" },
    });
    // Wait for the dropdown to appear.
    const option = await screen.findByText("White Chicks");
    fireEvent.mouseDown(option);

    expect(screen.getByLabelText("Title")).toHaveValue("White Chicks");
    expect(screen.getByLabelText(/description/i)).toHaveValue(
      "Two FBI agents go undercover as white women.",
    );
    // Genres are lowercased on import.
    expect(screen.getByText("comedy")).toBeInTheDocument();
    expect(screen.getByText("action")).toBeInTheDocument();
  });

  it("does not fire a new search after a result is selected", async () => {
    vi.mocked(searchMedia).mockResolvedValue([WHITE_CHICKS]);
    render(<AddPage />);
    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "White" },
    });
    const option = await screen.findByText("White Chicks");
    fireEvent.mouseDown(option);

    // Reset the call count, then wait to see if another search fires.
    vi.mocked(searchMedia).mockClear();
    await new Promise((r) => setTimeout(r, 500));
    expect(searchMedia).not.toHaveBeenCalled();
  });
});
