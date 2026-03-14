/**
 * Utility functions for testing TaskLogs backend connection
 */

import { API_BASE_URL, ENDPOINTS } from '$lib/config.js';

export interface ConnectionTestResult {
	success: boolean;
	message: string;
	url?: string;
	details?: string;
}

/**
 * Test basic HTTP connection to the backend
 */
export async function testHealthCheck(): Promise<ConnectionTestResult> {
	try {
		const url = `${API_BASE_URL}/health`;
		const response = await fetch(url);

		if (response.ok) {
			return {
				success: true,
				message: 'Health check passed',
				url,
				details: `HTTP ${response.status}`
			};
		}

		return {
			success: false,
			message: 'Health check failed',
			url,
			details: `HTTP ${response.status} - ${response.statusText}`
		};
	} catch (error) {
		return {
			success: false,
			message: 'Health check error',
			details: error instanceof Error ? error.message : String(error)
		};
	}
}

/**
 * Test EventSource connection to the task logs endpoint
 */
export function testEventSourceConnection(): Promise<ConnectionTestResult> {
	return new Promise((resolve) => {
		const taskLogsUrl = `${API_BASE_URL}${ENDPOINTS.runTask}`;

		const timeout = setTimeout(() => {
			eventSource.close();
			resolve({
				success: false,
				message: 'EventSource connection timeout (5s)',
				url: taskLogsUrl,
				details: 'No response received within 5 seconds'
			});
		}, 5000);

		try {
			const eventSource = new EventSource(taskLogsUrl);

			eventSource.onopen = () => {
				clearTimeout(timeout);
				eventSource.close();
				resolve({
					success: true,
					message: 'EventSource connection successful',
					url: taskLogsUrl,
					details: 'Connected and received onopen event'
				});
			};

			eventSource.onerror = () => {
				clearTimeout(timeout);
				const details = `ReadyState: ${eventSource.readyState} (0=CONNECTING, 1=OPEN, 2=CLOSED)`;
				eventSource.close();
				resolve({
					success: false,
					message: 'EventSource connection failed',
					url: taskLogsUrl,
					details
				});
			};
		} catch (error) {
			clearTimeout(timeout);
			resolve({
				success: false,
				message: 'EventSource creation error',
				url: taskLogsUrl,
				details: error instanceof Error ? error.message : String(error)
			});
		}
	});
}

/**
 * Run all connection tests
 */
export async function runAllConnectionTests(): Promise<ConnectionTestResult[]> {
	const results: ConnectionTestResult[] = [];

	// Test 1: Health check
	console.log('Running health check...');
	const healthResult = await testHealthCheck();
	results.push(healthResult);
	console.log('Health check:', healthResult);

	// Test 2: EventSource connection
	console.log('Running EventSource connection test...');
	const eventSourceResult = await testEventSourceConnection();
	results.push(eventSourceResult);
	console.log('EventSource test:', eventSourceResult);

	return results;
}

/**
 * Log test results in a formatted way
 */
export function logTestResults(results: ConnectionTestResult[]): void {
	console.group('TaskLogs Connection Test Results');

	results.forEach((result, index) => {
		const status = result.success ? '✓ PASS' : '✗ FAIL';
		console.group(`${status} - Test ${index + 1}`);
		console.log('Message:', result.message);
		if (result.url) console.log('URL:', result.url);
		if (result.details) console.log('Details:', result.details);
		console.groupEnd();
	});

	const passCount = results.filter((r) => r.success).length;
	const totalCount = results.length;
	console.log(`\nSummary: ${passCount}/${totalCount} tests passed`);

	console.groupEnd();
}
