import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json(
    { error: { code: "NOT_IMPLEMENTED", message: "TODO(phase-1)" } },
    { status: 501 }
  );
}

export async function POST() {
  return NextResponse.json(
    { error: { code: "NOT_IMPLEMENTED", message: "TODO(phase-1)" } },
    { status: 501 }
  );
}
