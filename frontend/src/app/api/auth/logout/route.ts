import { NextRequest, NextResponse } from "next/server";
import { deleteSession } from "@/src/lib/session";
import {
	getClientIp,
	isRateLimited,
	withTimeout,
} from "@/src/lib/server.lib";

export async function GET(req: NextRequest) {
	if (await isRateLimited(await getClientIp(req))) {
		return NextResponse.json({ error: "Too many requests" }, { status: 429 });
	}

	const timeoutMs = Number(process.env.HANDLER_TIMEOUT_MS ?? 5_000);

	try {
		await withTimeout(deleteSession(), timeoutMs);
		return NextResponse.redirect(new URL("/login", req.url));
	} catch (err) {
		const isTimeout =
			err instanceof Error && err.message.startsWith("Timeout apres");
		return NextResponse.json(
			{ error: isTimeout ? "Request timed out" : "Internal server error" },
			{ status: isTimeout ? 504 : 500 },
		);
	}
}

