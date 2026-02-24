import { Film, MessageSquare } from "lucide-react";
import Link from "next/link";
import { ThemeToggle } from "@/components/theme-toggle";

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="flex justify-end p-4">
        <ThemeToggle />
      </header>

      <main className="flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center gap-8 px-4">
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight">Pop's Choice 🍿</h1>
          <p className="mt-2 text-muted-foreground">
            AI-powered movie and series picker for us.
          </p>
        </div>

        <div className="flex w-full max-w-sm flex-col gap-3 sm:flex-row">
          <Link
            href="/add"
            className="flex flex-1 items-center justify-center gap-2 rounded-md bg-primary py-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            <Film className="h-4 w-4" />
            Log Watched
          </Link>
          <Link
            href="/recommend"
            className="flex flex-1 items-center justify-center gap-2 rounded-md border border-border bg-background py-4 text-sm font-medium transition-colors hover:bg-secondary"
          >
            <MessageSquare className="h-4 w-4" />
            Get Recommendation
          </Link>
        </div>
      </main>
    </div>
  );
}
