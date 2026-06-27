"use client";

import { unstable_rethrow } from "next/navigation";
import { Component, type ReactNode } from "react";

/**
 * Props for the ErrorBoundary component.
 *
 * @property fallback - The UI to display when an error is caught.
 * @property children - The child components to render.
 */
interface Props {
	fallback: ReactNode;
	children: ReactNode;
}

/**
 * Internal state for the ErrorBoundary component.
 */
interface State {
	hasError: boolean;
}

/**
 * An error boundary that catches errors in child components and displays a fallback UI.
 *
 * Allows Next.js control-flow errors (like redirects) to bubble up properly.
 */
export class ErrorBoundary extends Component<Props, State> {
	constructor(props: Props) {
		super(props);
		this.state = { hasError: false };
	}

	static getDerivedStateFromError(error: unknown): State {
		// Let Next.js control-flow errors (e.g. NEXT_REDIRECT thrown by
		// redirect()) bubble up to the framework instead of rendering the
		// fallback UI, so an expired session redirects to /login.
		unstable_rethrow(error);
		return { hasError: true };
	}

	override render() {
		if (this.state.hasError) {
			return this.props.fallback;
		}
		return this.props.children;
	}
}
