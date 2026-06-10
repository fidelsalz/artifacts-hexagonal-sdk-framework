<script lang="ts">
	import { API_BASE } from '$lib/config';
	import AppNav from '$lib/components/AppNav.svelte';
	import { onMount } from 'svelte';

	type Campaign = {
		slug: string;
		name: string;
		created_at: string;
		path: string;
		variations_generated: number;
	};

	let basePath = $state('');
	let setupInput = $state('');
	let setupError = $state('');
	let setupLoading = $state(false);
	let loadError = $state('');

	let campaigns = $state<Campaign[]>([]);
	let listLoading = $state(false);
	let listError = $state('');

	function formatDate(iso: string) {
		return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
	}

	async function loadSettings() {
		try {
			const res = await fetch(`${API_BASE}/api/settings`);
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			const data = await res.json();
			basePath = data.base_path ?? '';
		} catch (e) {
			loadError = e instanceof Error ? e.message : String(e);
		}
	}

	async function loadCampaigns() {
		listLoading = true;
		listError = '';
		try {
			const res = await fetch(`${API_BASE}/api/campaigns`);
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			campaigns = await res.json();
		} catch (e) {
			listError = e instanceof Error ? e.message : String(e);
		} finally {
			listLoading = false;
		}
	}

	async function saveBasePath() {
		setupLoading = true;
		setupError = '';
		try {
			const res = await fetch(`${API_BASE}/api/settings`, {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ base_path: setupInput.trim() }),
			});
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			basePath = setupInput.trim();
			await loadCampaigns();
		} catch (e) {
			setupError = e instanceof Error ? e.message : String(e);
		} finally {
			setupLoading = false;
		}
	}

	onMount(async () => {
		await loadSettings();
		if (!basePath && import.meta.env.VITE_BASE_PATH) {
			setupInput = import.meta.env.VITE_BASE_PATH;
			await saveBasePath();
		} else if (basePath) {
			await loadCampaigns();
		}
	});
</script>

<div class="min-h-screen bg-white">
	<AppNav>
		{#snippet right()}
			{#if basePath}
				<a
					href="/new-campaign"
					class="bg-emerald-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-emerald-500 transition-colors shadow-sm shadow-emerald-100"
				>
					+ New Campaign
				</a>
			{/if}
		{/snippet}
	</AppNav>

	<main class="px-8 py-8 max-w-3xl mx-auto">
		{#if loadError}
			<div class="rounded-xl border border-red-200 bg-red-50 px-5 py-4 mb-6 text-sm text-red-700">
				Cannot reach backend: {loadError}
			</div>
		{/if}
		<!-- Setup banner -->
		{#if !basePath && !loadError}
			<div class="rounded-xl border border-slate-200 bg-slate-50 p-6">
				<h2 class="text-sm font-semibold text-slate-800 mb-1">Set campaigns folder</h2>
				<p class="text-sm text-slate-500 mb-4">Enter the absolute path where campaign folders will be created and stored.</p>
				<form onsubmit={(e) => { e.preventDefault(); saveBasePath(); }} class="flex gap-2">
					<input
						type="text"
						bind:value={setupInput}
						placeholder="/absolute/path/to/campaigns"
						class="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500"
					/>
					<button
						type="submit"
						disabled={setupLoading || !setupInput.trim()}
						class="bg-emerald-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-emerald-500 transition-colors shadow-sm shadow-emerald-100 disabled:opacity-50"
					>
						{setupLoading ? 'Saving…' : 'Save'}
					</button>
				</form>
				{#if setupError}
					<p class="mt-2 text-sm text-red-600">{setupError}</p>
				{/if}
			</div>
		{:else}
			<!-- Campaign list -->
			{#if listLoading}
				<p class="text-sm text-slate-400">Loading campaigns…</p>
			{:else if listError}
				<p class="text-sm text-red-600">{listError}</p>
			{:else if campaigns.length === 0}
				<div class="text-center py-16">
					<p class="text-slate-400 text-sm">No campaigns yet — create one to get started.</p>
					<a href="/new-campaign" class="mt-4 inline-block bg-emerald-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-emerald-500 transition-colors shadow-sm shadow-emerald-100">
						+ New Campaign
					</a>
				</div>
			{:else}
				<div class="rounded-xl border border-slate-200 overflow-hidden">
					{#each campaigns as campaign}
						<a
							href="/campaigns/{campaign.slug}"
							target="_blank"
							rel="noopener noreferrer"
							class="flex items-center gap-4 px-5 py-4 hover:bg-slate-50 border-b border-slate-200/60 transition-colors last:border-b-0"
						>
							<div class="flex-1 min-w-0">
								<div class="flex items-center gap-2">
									<span class="font-semibold text-slate-900 text-sm truncate">{campaign.name}</span>
									<span class="bg-slate-100 text-slate-700 text-xs font-semibold rounded-full px-2.5 py-0.5 shrink-0">{campaign.slug}</span>
								</div>
								<p class="text-xs text-slate-400 mt-0.5">{formatDate(campaign.created_at)}</p>
							</div>
							<div class="shrink-0 text-right">
								{#if campaign.variations_generated > 0}
									<span class="bg-slate-100 text-slate-700 text-xs font-semibold rounded-full px-2.5 py-0.5">
										{campaign.variations_generated} variation{campaign.variations_generated !== 1 ? 's' : ''}
									</span>
								{:else}
									<span class="text-xs text-slate-300">no variations</span>
								{/if}
							</div>
							<span class="text-slate-300 shrink-0">↗</span>
						</a>
					{/each}
				</div>
			{/if}
		{/if}
	</main>
</div>
