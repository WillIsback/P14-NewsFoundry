import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merges Tailwind CSS classes together.
 *
 * @param inputs - The class values to merge.
 * @returns The merged class string.
 */
export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}
