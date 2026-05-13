import { cookies } from "next/headers";
import { type NextRequest, NextResponse } from "next/server";
import { decrypt } from "@/src/lib/session";

// 1. Specify protected and public routes
const protectedRoutes = new Set(["/home", "/test"]);
const publicRoutes = new Set(["/login", "/signup", "/"]);

export default async function proxy(req: NextRequest) {
	// 2. Check if the current route is protected or public
	const path = req.nextUrl.pathname;
	const isProtectedRoute = protectedRoutes.has(path);
	const isPublicRoute = publicRoutes.has(path);

	// 3. Decrypt the session from the cookie
	const cookie = (await cookies()).get("session")?.value;
	const session = await decrypt(cookie);

	// 4. Redirect to /login if the user is not authenticated
	if ((isProtectedRoute || path === "/") && !session?.userId) {
		return NextResponse.redirect(new URL("/login", req.nextUrl));
	}

	// 5. Redirect to /home if the user is authenticated
	if (
		isPublicRoute &&
		session?.userId &&
		!req.nextUrl.pathname.startsWith("/home")
	) {
		return NextResponse.redirect(new URL("/home", req.nextUrl));
	}

	return NextResponse.next();
}

// Routes Proxy should not run on
export const config = {
	matcher: ["/((?!api|_next/static|_next/image|.*\\.png$).*)"],
};
