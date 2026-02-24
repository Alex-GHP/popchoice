import { NextResponse } from "next/server";

const BACKEND = process.env.API_URL ?? "http://localhost:8000";
const SECRET = process.env.API_SECRET ?? "";

export async function POST() {
  const res = await fetch(`${BACKEND}/recommend/start`, {
    method: "POST",
    headers: { Authorization: `Bearer ${SECRET}` },
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
