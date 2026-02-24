"use client";

import { ArrowLeft, Send } from "lucide-react";
import Link from "next/link";
import { useRef, useState } from "react";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { sendReply, startRecommendation } from "@/lib/api";

interface Message {
  id: number;
  role: "agent" | "user";
  text: string;
}

export default function RecommendPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [recommendation, setRecommendation] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const idCounter = useRef(0);

  function nextId() {
    idCounter.current += 1;
    return idCounter.current;
  }

  async function handleStart() {
    setLoading(true);
    setError(null);
    try {
      const data = await startRecommendation();
      setThreadId(data.thread_id);
      setMessages([{ id: nextId(), role: "agent", text: data.question }]);
    } catch {
      setError("Could not connect to the backend. Make sure it is running.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || !threadId || loading) return;

    const answer = input.trim();
    setMessages((m) => [...m, { id: nextId(), role: "user", text: answer }]);
    setInput("");
    setLoading(true);

    try {
      const data = await sendReply(threadId, answer);
      if (data.done) {
        setDone(true);
        setRecommendation(data.recommendation ?? null);
      } else {
        setMessages((m) => [
          ...m,
          { id: nextId(), role: "agent", text: data.question ?? "" },
        ]);
      }
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setMessages([]);
    setThreadId(null);
    setInput("");
    setLoading(false);
    setDone(false);
    setRecommendation(null);
    setError(null);
    idCounter.current = 0;
  }

  const started = messages.length > 0 || done;

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
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

      <main className="mx-auto flex w-full max-w-lg flex-1 flex-col px-4 pb-6">
        <h1 className="mb-6 text-2xl font-bold">What should we watch?</h1>

        {/* Pre-start state */}
        {!started && !loading && (
          <div className="flex flex-1 flex-col items-center justify-center gap-4">
            <p className="text-center text-muted-foreground">
              Pop will ask you a few questions to find the perfect pick.
            </p>
            <Button onClick={handleStart}>Start</Button>
          </div>
        )}

        {/* Loading spinner before first message */}
        {!started && loading && (
          <div className="flex flex-1 items-center justify-center">
            <span className="text-sm text-muted-foreground">Thinking...</span>
          </div>
        )}

        {/* Chat area */}
        {started && (
          <div className="flex flex-1 flex-col gap-3">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`max-w-[80%] rounded-lg px-4 py-2.5 text-sm ${
                  m.role === "agent"
                    ? "self-start bg-secondary text-secondary-foreground"
                    : "self-end bg-primary text-primary-foreground"
                }`}
              >
                {m.text}
              </div>
            ))}

            {loading && (
              <div className="self-start rounded-lg bg-secondary px-4 py-2.5 text-sm text-muted-foreground">
                Thinking...
              </div>
            )}

            {done && recommendation && (
              <div className="mt-2 rounded-lg border border-border p-4">
                <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                  Recommendation
                </p>
                <p className="text-sm leading-relaxed">{recommendation}</p>
              </div>
            )}
          </div>
        )}

        {error && <p className="mt-4 text-sm text-destructive">{error}</p>}

        {/* Input or reset */}
        {done ? (
          <Button
            onClick={handleReset}
            variant="outline"
            className="mt-6 w-full"
          >
            Start over
          </Button>
        ) : started && !loading ? (
          <form onSubmit={handleSend} className="mt-4 flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your answer..."
              autoFocus
            />
            <Button
              type="submit"
              size="icon"
              disabled={!input.trim()}
              aria-label="Send"
            >
              <Send className="h-4 w-4" />
            </Button>
          </form>
        ) : null}
      </main>
    </div>
  );
}
