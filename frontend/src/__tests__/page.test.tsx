import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import Home from "@/app/page";

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    className,
  }: {
    href: string;
    children: React.ReactNode;
    className?: string;
  }) => (
    <a href={href} className={className}>
      {children}
    </a>
  ),
}));

vi.mock("@/components/theme-toggle", () => ({
  ThemeToggle: () => <button type="button">Toggle theme</button>,
}));

vi.mock("lucide-react", () => ({
  Film: () => <span data-testid="film-icon" />,
  MessageSquare: () => <span data-testid="message-icon" />,
}));

describe("Home page", () => {
  it("renders the app title", () => {
    render(<Home />);
    expect(
      screen.getByRole("heading", { name: /pop.*choice/i }),
    ).toBeInTheDocument();
  });

  it("has a link to the add page", () => {
    render(<Home />);
    const link = screen.getByRole("link", { name: /log watched/i });
    expect(link).toHaveAttribute("href", "/add");
  });

  it("has a link to the recommend page", () => {
    render(<Home />);
    const link = screen.getByRole("link", { name: /get recommendation/i });
    expect(link).toHaveAttribute("href", "/recommend");
  });

  it("renders the theme toggle", () => {
    render(<Home />);
    expect(screen.getByText("Toggle theme")).toBeInTheDocument();
  });
});
