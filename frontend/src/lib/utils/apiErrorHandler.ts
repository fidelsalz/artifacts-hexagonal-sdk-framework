/**
 * Global API error handler utilities
 * Automatically detect 401 errors and trigger token refresh modal
 */

import { openTokenRefreshModal } from '$lib/stores/tokenRefreshModal';

/**
 * Check if an error is a 401 authentication error
 */
export function is401Error(error: any): boolean {
	if (!error) return false;

	// Check status code
	if (error.status === 401) return true;

	// Check error message
	const message = error.message?.toLowerCase() || '';
	if (message.includes('401') || message.includes('unauthorized')) return true;

	// Check response text
	const text = error.statusText?.toLowerCase() || '';
	if (text.includes('unauthorized')) return true;

	return false;
}

/**
 * Handle API errors globally
 * Returns true if error was handled (401), false otherwise
 */
export function handleApiError(error: any, source: string): boolean {
	if (is401Error(error)) {
		openTokenRefreshModal(
			'API authentication failed. Your tokens may have expired.',
			source
		);
		return true;
	}
	return false;
}

/**
 * Wrapper for fetch that automatically handles 401 errors
 * Usage: const response = await fetchWithErrorHandling(url, options, 'Component Name');
 */
export async function fetchWithErrorHandling(
	url: string,
	options?: RequestInit,
	source: string = 'API Call'
): Promise<Response> {
	try {
		const response = await fetch(url, options);

		// Check for 401 error
		if (response.status === 401) {
			openTokenRefreshModal(
				'API authentication failed. Your tokens may have expired.',
				source
			);
			throw new Error('Authentication required');
		}

		return response;
	} catch (error) {
		// Handle network errors or other fetch failures
		if (error instanceof Error && error.message !== 'Authentication required') {
			handleApiError(error, source);
		}
		throw error;
	}
}

/**
 * Parse error from response for user-friendly display
 */
export async function parseErrorMessage(response: Response): Promise<string> {
	try {
		const data = await response.json();
		return data.detail || data.message || `HTTP ${response.status}: ${response.statusText}`;
	} catch {
		return `HTTP ${response.status}: ${response.statusText}`;
	}
}