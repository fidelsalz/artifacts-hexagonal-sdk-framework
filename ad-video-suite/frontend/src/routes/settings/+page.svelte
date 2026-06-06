<script lang="ts">
	import { API_BASE } from '$lib/config';
	import AppNav from '$lib/components/AppNav.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import Label from '$lib/components/ui/label.svelte';
	import { onMount } from 'svelte';

	let basePath = $state('');
	let maxActiveCampaigns = $state(3);

	let saving = $state(false);
	let saved = $state(false);
	let error = $state('');

	onMount(async () => {
		try {
			const res = await fetch(`${API_BASE}/api/settings`);
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			const data = await res.json();
			basePath = data.base_path ?? '';
			maxActiveCampaigns = data.max_active_campaigns ?? 3;
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	});

	async function save() {
		if (!basePath.trim()) {
			error = 'Campaigns folder path is required.';
			return;
		}
		saving = true;
		saved = false;
		error = '';
		try {
			const res = await fetch(`${API_BASE}/api/settings`, {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					base_path: basePath.trim(),
					max_active_campaigns: maxActiveCampaigns,
				}),
			});
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			saved = true;
			setTimeout(() => (saved = false), 3000);
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			saving = false;
		}
	}
</script>

<div class="min-h-screen bg-white">
	<AppNav />

	<main class="px-8 py-10 max-w-xl mx-auto">
		<h1 class="text-lg font-semibold text-slate-900 mb-1">Settings</h1>
		<p class="text-sm text-slate-500 mb-8">Configure the Ad Video Suite backend.</p>

		<form onsubmit={(e) => { e.preventDefault(); save(); }} class="space-y-6">

			<!-- base_path -->
			<div class="space-y-2">
				<Label for="base-path">Campaigns folder</Label>
				<Input
					id="base-path"
					type="text"
					bind:value={basePath}
					placeholder="/absolute/path/to/campaigns"
				/>
				<p class="text-xs text-slate-400">
					Absolute path on the server where campaign folders are created. All
					C001, C002… slugs live here.
				</p>
			</div>

			<!-- max_active_campaigns -->
			<div class="space-y-2">
				<Label for="max-campaigns">Max active campaigns</Label>
				<Input
					id="max-campaigns"
					type="number"
					min="1"
					max="99"
					class="w-24"
					bind:value={maxActiveCampaigns}
				/>
				<p class="text-xs text-slate-400">
					How many campaigns can have open agent sessions simultaneously.
					Exceeding this limit returns an error when trying to launch a new
					agent session.
				</p>
			</div>

			{#if error}
				<p class="text-sm text-red-600">{error}</p>
			{/if}

			<div class="flex items-center gap-3 pt-1">
				<Button type="submit" disabled={saving}>
					{saving ? 'Saving…' : 'Save settings'}
				</Button>
				{#if saved}
					<span class="text-sm text-emerald-600 font-medium">Saved ✓</span>
				{/if}
			</div>
		</form>
	</main>
</div>
