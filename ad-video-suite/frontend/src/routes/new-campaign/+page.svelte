<script lang="ts">
	import { goto } from '$app/navigation';
	import { API_BASE } from '$lib/config';
	import { onMount } from 'svelte';

	let name = $state('');
	let submitting = $state(false);
	let error = $state('');

	onMount(async () => {
		const res = await fetch(`${API_BASE}/api/settings`);
		const data = await res.json();
		if (!data.base_path) goto('/');
	});

	async function submit() {
		submitting = true;
		error = '';
		try {
			const res = await fetch(`${API_BASE}/api/campaigns`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ name: name.trim() || undefined }),
			});
			if (!res.ok) {
				const data = await res.json().catch(() => ({}));
				throw new Error(data.detail ?? `HTTP ${res.status}`);
			}
			const campaign = await res.json();
			goto(`/campaigns/${campaign.slug}`);
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
			submitting = false;
		}
	}
</script>

<div class="min-h-screen bg-white">
	<header class="border-b border-slate-200/60 px-8 py-5">
		<a href="/" class="text-sm text-slate-400 hover:text-slate-700 transition-colors">← Campaigns</a>
	</header>

	<main class="px-8 py-10 max-w-lg mx-auto">
		<h1 class="text-xl font-semibold text-slate-900 mb-6">New Campaign</h1>

		<form onsubmit={(e) => { e.preventDefault(); submit(); }} class="space-y-5">
			<div>
				<label for="campaign-name" class="block text-sm font-medium text-slate-700 mb-1.5">
					Campaign name <span class="text-slate-400 font-normal">(optional)</span>
				</label>
				<input
					id="campaign-name"
					type="text"
					bind:value={name}
					placeholder="e.g. Running Shoes Q4"
					class="w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500"
				/>
				<p class="mt-1.5 text-xs text-slate-400">A slug like C001 is auto-generated. The name is just a label.</p>
			</div>

			{#if error}
				<p class="text-sm text-red-600">{error}</p>
			{/if}

			<div class="flex items-center gap-3 pt-1">
				<button
					type="submit"
					disabled={submitting}
					class="bg-emerald-600 text-white text-sm font-medium px-5 py-2.5 rounded-lg hover:bg-emerald-500 transition-colors shadow-sm shadow-emerald-100 disabled:opacity-50"
				>
					{submitting ? 'Creating…' : 'Create campaign'}
				</button>
				<a href="/" class="text-sm text-slate-400 hover:text-slate-700 transition-colors">Cancel</a>
			</div>
		</form>
	</main>
</div>
