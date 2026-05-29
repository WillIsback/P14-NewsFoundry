import { cookies } from "next/headers";
import { type NextRequest, NextResponse } from "next/server";
import { decrypt } from "@/src/lib/session";

// 1. Specify protected and public routes
// All routes under (private) group are protected; match by prefix
const publicRoutes = new Set(["/login", "/signup", "/"]);

export const config = {
	matcher: [
		/*
		 * Match all request paths EXCEPT:
		 * - _next/static (static files: CSS, JS, fonts…)
		 * - _next/image  (image optimisation)
		 * - favicon.ico and common static extensions
		 */
		"/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)",
	],
};

export default async function proxy(req: NextRequest) {
	// 2. Check if the current route is protected or public
	const path = req.nextUrl.pathname;
	const isPublicRoute = publicRoutes.has(path);
	// Any route that is not explicitly public is considered protected
	const isProtectedRoute = !isPublicRoute;

	// 3. Decrypt the session from the cookie
	const cookie = (await cookies()).get("session")?.value;
	const session = await decrypt(cookie);

	// 4. Redirect to /login if the user is not authenticated
	if (isProtectedRoute && !session?.userId) {
		return NextResponse.redirect(new URL("/login", req.nextUrl));
	}

	// 5. Redirect to /login if the user is not authenticated
	if (
		isPublicRoute &&
		!session?.userId &&
		!req.nextUrl.pathname.startsWith("/login")
	) {
		return NextResponse.redirect(new URL("/login", req.nextUrl));
	}
	// 6. Redirect to /home if the user is authenticated
	if (
		isPublicRoute &&
		session?.userId &&
		!req.nextUrl.pathname.startsWith("/home")
	) {
		return NextResponse.redirect(new URL("/home", req.nextUrl));
	}

	return NextResponse.next();
}
