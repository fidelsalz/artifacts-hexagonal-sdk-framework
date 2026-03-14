<script lang="ts">
	import { onMount } from 'svelte';
	import { API_BASE_URL } from '$lib/config.js';

	let logs = $state<string[]>([]);
	let isConnected = $state(false);
	let isLoading = $state(false);
	let evtSource: EventSource | null = null;

	onMount(() => {
		evtSource = new EventSource(`${API_BASE_URL}/run-task`);

		evtSource.onopen = () => {
			isConnected = true;
		};

		evtSource.onmessage = (event: MessageEvent) => {
			logs = [...logs, event.data];
		};

		evtSource.onerror = () => {
			isConnected = false;
		};

		return () => evtSource?.close();
	});

	async function startTask() {
		isLoading = true;
		try {
			const response = await fetch(`${API_BASE_URL}/api/test-task`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' }
			});
			if (!response.ok) throw new Error(response.statusText);
		} catch (error) {
			console.error('Error starting task:', error);
		} finally {
			isLoading = false;
		}
	}
</script>

<h2>Live Task Output</h2>

<div class="controls">
	<button onclick={startTask} disabled={isLoading}>
		{isLoading ? 'Starting...' : 'Start Task'}
	</button>
	<span class={isConnected ? 'status' : 'status-disconnected'}>
		{isConnected ? 'Connected' : 'Disconnected'}
	</span>
</div>

<div class="logs-container">
	{#if logs.length === 0}
		<p class="empty-message">No logs yet. Click "Start Task" to begin.</p>
	{:else}
		{#each logs as line, i}
			<p class="log-line">{line}</p>
		{/each}
	{/if}
</div>

<style>
	h2 { margin-bottom: 1rem; }

	.controls {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 2rem;
		align-items: center;
	}

	button {
		padding: 0.5rem 1rem;
		background-color: #007bff;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 1rem;
	}

	button:hover:not(:disabled) { background-color: #0056b3; }
	button:disabled { background-color: #ccc; cursor: not-allowed; }

	.status { color: #28a745; font-weight: bold; }
	.status-disconnected { color: #dc3545; font-weight: bold; }

	.logs-container {
		background-color: #f5f5f5;
		border: 1px solid #ddd;
		border-radius: 4px;
		padding: 1rem;
		max-height: 600px;
		overflow-y: auto;
		font-family: 'Courier New', monospace;
		font-size: 0.9rem;
	}

	.log-line { margin: 0.25rem 0; word-break: break-word; }
	.empty-message { color: #999; font-style: italic; }
</style>
