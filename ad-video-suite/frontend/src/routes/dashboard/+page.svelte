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

	type SessionEntry = {
		session_key: string;
		campaign: string;
		agent_id: string;
		cwd: string;
		started_at: string;
	};

	type SessionsData = {
		active_campaigns: string[];
		sessions: SessionEntry[];
	};

	let campaigns = $state<Campaign[]>([]);
	let sessionsData = $state<SessionsData>({ active_campaigns: [], sessions: [] });
	let loading = $state(false);
	let error = $state('');

	const totalVariations = $derived(campaigns.reduce((s, c) => s + c.variations_generated, 0));

	async function load() {
		loading = true;
		error = '';
		try {
			const [cRes, sRes] = await Promise.all([
				fetch(`${API_BASE}/api/campaigns`),
				fetch(`${API_BASE}/api/sessions`),
			]);
			if (!cRes.ok) throw new Error(`Campaigns: HTTP ${cRes.status}`);
			if (!sRes.ok) throw new Error(`Sessions: HTTP ${sRes.status}`);
			campaigns = await cRes.json();
			sessionsData = await sRes.json();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			loading = false;
		}
	}

	onMount(load);

	function elapsed(iso: string): string {
		const secs = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
		if (secs < 60) return `${secs}s`;
		const mins = Math.floor(secs / 60);
		if (mins < 60) return `${mins}m`;
		return `${Math.floor(mins / 60)}h ${mins % 60}m`;
	}

	function shortCwd(cwd: string): string {
		return cwd.split('/').slice(-2).join('/');
	}
</script>

<div class="min-h-screen bg-white">
	<AppNav />

	<main class="px-8 py-8 max-w-5xl mx-auto space-y-8">

		<!-- Heading row -->
		<div class="flex items-center justify-between">
			<h1 class="text-lg font-semibold text-slate-900">Dashboard</h1>
			<button
				onclick={load}
				disabled={loading}
				class="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg
				       border border-slate-200 text-slate-600 hover:bg-slate-100 transition-colors
				       disabled:opacity-50 disabled:cursor-not-allowed"
			>
				<span class={loading ? 'animate-spin inline-block' : ''}>↺</span>
				{loading ? 'Refreshing…' : 'Refresh'}
			</button>
		</div>

		{#if error}
			<p class="text-sm text-red-600">{error}</p>
		{/if}

		<!-- Stat cards -->
		<div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
			{#each [
				{ label: 'Campaigns', value: campaigns.length },
				{ label: 'Variations', value: totalVariations },
				{ label: 'Live sessions', value: sessionsData.sessions.length },
				{ label: 'Active campaigns', value: sessionsData.active_campaigns.length },
			] as card}
				<div class="rounded-xl border border-slate-200 bg-white px-5 py-4">
					<p class="text-[11px] font-semibold uppercase tracking-wide text-slate-400 mb-1">{card.label}</p>
					<p class="text-3xl font-bold text-slate-900 tabular-nums">
						{loading ? '—' : card.value}
					</p>
				</div>
			{/each}
		</div>

		<!-- Live sessions -->
		<section>
			<h2 class="text-sm font-semibold text-slate-700 mb-3">
				Live sessions
				{#if sessionsData.sessions.length > 0}
					<span class="ml-1.5 inline-flex items-center gap-1 text-[10px] font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2 py-0.5">
						<span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
						{sessionsData.sessions.length} running
					</span>
				{/if}
			</h2>

			{#if sessionsData.sessions.length === 0}
				<div class="rounded-xl border border-slate-200 px-5 py-6 text-center">
					<p class="text-sm text-slate-400 italic">No agents running.</p>
				</div>
			{:else}
				<div class="rounded-xl border border-slate-200 overflow-hidden">
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b border-slate-200 bg-slate-50">
								<th class="text-left px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400">Campaign</th>
								<th class="text-left px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400">Agent</th>
								<th class="text-left px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400">Folder</th>
								<th class="text-left px-4 py-2.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400">Running for</th>
							</tr>
						</thead>
						<tbody>
							{#each sessionsData.sessions as s (s.session_key)}
								<tr class="border-b border-slate-100 last:border-b-0 hover:bg-slate-50 transition-colors">
									<td class="px-4 py-2.5">
										<span class="bg-slate-100 text-slate-700 text-xs font-semibold rounded-full px-2 py-0.5">{s.campaign}</span>
									</td>
									<td class="px-4 py-2.5 text-xs font-medium text-slate-800">{s.agent_id}</td>
									<td class="px-4 py-2.5 text-xs font-mono text-slate-500">{shortCwd(s.cwd)}</td>
									<td class="px-4 py-2.5 text-xs text-slate-500">{elapsed(s.started_at)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</section>

	</main>
</div>
