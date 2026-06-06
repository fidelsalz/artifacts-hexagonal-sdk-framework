<script lang="ts">
	import { API_BASE } from '$lib/config';

	type Check = { label: string; url: string; status: 'idle' | 'ok' | 'error'; data?: unknown; error?: string };

	let checks = $state<Check[]>([
		{ label: 'Health', url: '/health', status: 'idle' },
		{ label: 'Settings', url: '/api/settings', status: 'idle' },
		{ label: 'Campaigns', url: '/api/campaigns', status: 'idle' },
		{ label: 'Tree', url: '/api/tree', status: 'idle' },
		{ label: 'Agents', url: '/api/agents', status: 'idle' },
	]);

	let running = $state(false);

	async function runAll() {
		running = true;
		for (const check of checks) {
			check.status = 'idle';
			check.data = undefined;
			check.error = undefined;
		}
		await Promise.all(
			checks.map(async (check) => {
				try {
					const res = await fetch(`${API_BASE}${check.url}`);
					const data = await res.json();
					if (res.ok) {
						check.status = 'ok';
						check.data = data;
					} else {
						check.status = 'error';
						check.error = `HTTP ${res.status}`;
						check.data = data;
					}
				} catch (e) {
					check.status = 'error';
					check.error = e instanceof Error ? e.message : String(e);
				}
			})
		);
		running = false;
	}
</script>

<div class="min-h-screen bg-zinc-50 p-8">
	<div class="mx-auto max-w-2xl">
		<div class="mb-6 flex items-center justify-between">
			<div>
				<h1 class="text-xl font-semibold text-zinc-900">API Test</h1>
				<p class="text-sm text-zinc-500">{API_BASE}</p>
			</div>
			<button
				onclick={runAll}
				disabled={running}
				class="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 disabled:opacity-50"
			>
				{running ? 'Running…' : 'Run checks'}
			</button>
		</div>

		<div class="space-y-2">
			{#each checks as check}
				<div class="rounded-lg border border-zinc-200 bg-white p-4">
					<div class="flex items-center gap-3">
						<span class="text-lg">
							{check.status === 'ok' ? '✅' : check.status === 'error' ? '❌' : '⬜'}
						</span>
						<div class="flex-1">
							<span class="font-medium text-zinc-900">{check.label}</span>
							<span class="ml-2 text-sm text-zinc-400">{check.url}</span>
						</div>
						{#if check.error}
							<span class="text-sm text-red-600">{check.error}</span>
						{/if}
					</div>
					{#if check.data !== undefined}
						<pre class="mt-2 overflow-x-auto rounded bg-zinc-50 p-2 text-xs text-zinc-700">{JSON.stringify(check.data, null, 2)}</pre>
					{/if}
				</div>
			{/each}
		</div>
	</div>
</div>
