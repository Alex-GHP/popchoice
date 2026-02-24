import { type NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.API_URL ?? "http://localhost:8000";
const SECRET = process.env.API_SECRET ?? "";

export async function GET(req: NextRequest) {
  const q = req.nextUrl.searchParams.get("q") ?? "";
  const res = await fetch(`${BACKEND}/search?q=${encodeURIComponent(q)}`, {
    headers: { Authorization: `Bearer ${SECRET}` },
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
