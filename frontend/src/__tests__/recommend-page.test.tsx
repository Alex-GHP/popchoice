import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import RecommendPage from "@/app/recommend/page";
import { sendReply, startRecommendation } from "@/lib/api";

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
  Send: () => <span />,
}));

vi.mock("@/lib/api", () => ({
  startRecommendation: vi.fn(),
  sendReply: vi.fn(),
}));

describe("Recommend page", () => {
  beforeEach(() => {
    vi.mocked(startRecommendation).mockResolvedValue({
      thread_id: "thread-abc",
      question: "What mood are you in tonight?",
    });
    vi.mocked(sendReply).mockResolvedValue({
      done: false,
      question: "Movie or series?",
    });
  });

  it("renders the Start button before conversation begins", () => {
    render(<RecommendPage />);
    expect(screen.getByRole("button", { name: /start/i })).toBeInTheDocument();
  });

  it("shows the first agent question after clicking Start", async () => {
    render(<RecommendPage />);
    fireEvent.click(screen.getByRole("button", { name: /start/i }));
    await waitFor(() => {
      expect(
        screen.getByText("What mood are you in tonight?"),
      ).toBeInTheDocument();
    });
  });

  it("shows a text input for answering after conversation starts", async () => {
    render(<RecommendPage />);
    fireEvent.click(screen.getByRole("button", { name: /start/i }));
    await waitFor(() => {
      expect(
        screen.getByPlaceholderText("Type your answer..."),
      ).toBeInTheDocument();
    });
  });

  it("sends the reply and shows the next question", async () => {
    render(<RecommendPage />);
    fireEvent.click(screen.getByRole("button", { name: /start/i }));
    await waitFor(() => screen.getByPlaceholderText("Type your answer..."));

    const input = screen.getByPlaceholderText("Type your answer...");
    fireEvent.change(input, { target: { value: "relaxed" } });
    fireEvent.submit(input.closest("form") as HTMLElement);

    await waitFor(() => {
      expect(screen.getByText("Movie or series?")).toBeInTheDocument();
    });
    expect(sendReply).toHaveBeenCalledWith("thread-abc", "relaxed");
  });

  it("shows recommendation when the agent is done", async () => {
    vi.mocked(sendReply).mockResolvedValue({
      done: true,
      recommendation: "Watch Parasite — it perfectly matches your mood.",
    });

    render(<RecommendPage />);
    fireEvent.click(screen.getByRole("button", { name: /start/i }));
    await waitFor(() => screen.getByPlaceholderText("Type your answer..."));

    const input = screen.getByPlaceholderText("Type your answer...");
    fireEvent.change(input, { target: { value: "any" } });
    fireEvent.submit(input.closest("form") as HTMLElement);

    await waitFor(() => {
      expect(
        screen.getByText("Watch Parasite — it perfectly matches your mood."),
      ).toBeInTheDocument();
    });
  });

  it("shows a Start over button after the recommendation", async () => {
    vi.mocked(sendReply).mockResolvedValue({
      done: true,
      recommendation: "Watch Parasite.",
    });

    render(<RecommendPage />);
    fireEvent.click(screen.getByRole("button", { name: /start/i }));
    await waitFor(() => screen.getByPlaceholderText("Type your answer..."));

    const input = screen.getByPlaceholderText("Type your answer...");
    fireEvent.change(input, { target: { value: "any" } });
    fireEvent.submit(input.closest("form") as HTMLElement);

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /start over/i }),
      ).toBeInTheDocument();
    });
  });

  it("shows error message when API fails", async () => {
    vi.mocked(startRecommendation).mockRejectedValue(
      new Error("Network error"),
    );
    render(<RecommendPage />);
    fireEvent.click(screen.getByRole("button", { name: /start/i }));
    await waitFor(() => {
      expect(screen.getByText(/could not connect/i)).toBeInTheDocument();
    });
  });
});
