<script lang="ts">
	import { API_BASE } from '$lib/config';
	import {
		getSessionsForCwd,
		launchSession,
		sessionStore,
		setActiveSession,
	} from '$lib/stores/sessionStore.svelte';
	import type { AgentCandidate } from '$lib/types';
	import { onMount } from 'svelte';

	let {
		selectedPath,
		selectedAgents,
		campaign,
		onSessionLaunched,
	}: {
		selectedPath: string;
		selectedAgents: AgentCandidate[];
		campaign: string;
		onSessionLaunched: (key: string) => void;
	} = $props();

	// ---------- local state ----------
	let launching = $state<string | null>(null);
	let disambiguateCandidates = $state<AgentCandidate[] | null>(null);
	let disambiguateFor = $state<string | null>(null); // agentId that triggered disambiguation
	let launchError = $state('');
	let sessionCount = $state(0);
	let activeCampaigns = $state<string[]>([]);

	// Reactive: existing sessions for the selected folder
	const existingSessions = $derived(getSessionsForCwd(selectedPath));

	async function fetchSessions() {
		try {
			const res = await fetch(`${API_BASE}/api/sessions`);
			if (res.ok) {
				const data = await res.json();
				sessionCount = (data.sessions ?? []).length;
				activeCampaigns = data.active_campaigns ?? [];
			}
		} catch {
			// silent
		}
	}

	onMount(fetchSessions);

	$effect(() => {
		// Re-fetch when selected folder changes
		selectedPath;
		fetchSessions();
	});

	async function launch(agentId: string) {
		launchError = '';
		launching = agentId;
		disambiguateCandidates = null;
		try {
			const res = await fetch(`${API_BASE}/api/launch`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ path: selectedPath, agent_id: agentId }),
			});
			const data = await res.json();
			if (!res.ok) {
				launchError = data.detail ?? `HTTP ${res.status}`;
				return;
			}
			if (data.ambiguous) {
				disambiguateCandidates = data.candidates;
				disambiguateFor = null;
				return;
			}
			// Success
			launchSession(data.agent_id, data.agent_name, data.cwd, data.campaign, data.ws_url);
			const key = `${data.agent_id}::${data.cwd}`;
			onSessionLaunched(key);
			fetchSessions();
		} catch (e) {
			launchError = e instanceof Error ? e.message : String(e);
		} finally {
			launching = null;
		}
	}

	function resume(key: string) {
		setActiveSession(key);
		onSessionLaunched(key);
	}

	function folderName(path: string): string {
		return path.split('/').pop() ?? path;
	}
</script>

<div class="space-y-4">
	<!-- Header row -->
	<div class="flex items-center justify-between">
		<div>
			{#if selectedPath}
				<p class="text-xs font-semibold text-slate-700">
					Folder: <span class="font-mono text-slate-900">{folderName(selectedPath)}</span>
				</p>
			{:else}
				<p class="text-xs text-slate-400 italic">Select a folder in the tree.</p>
			{/if}
		</div>
		{#if sessionCount > 0}
			<span class="text-[10px] text-slate-400">{sessionCount} active session{sessionCount !== 1 ? 's' : ''} in campaign</span>
		{/if}
	</div>

	{#if selectedPath}
		<!-- Existing sessions for this folder -->
		{#if existingSessions.length > 0}
			<div class="space-y-1.5">
				<p class="text-[10px] font-semibold uppercase tracking-wide text-slate-400">Open sessions</p>
				{#each existingSessions as session (session.key)}
					<div class="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2">
						<span class="flex-1 min-w-0">
							<span class="text-xs font-semibold text-emerald-800">{session.agentName}</span>
							<span class="ml-2 text-[10px] font-mono text-emerald-600">{session.status}</span>
						</span>
						<button
							onclick={() => resume(session.key)}
							class="text-[11px] px-2.5 py-1 rounded-md bg-emerald-600 text-white font-medium hover:bg-emerald-500 transition-colors shrink-0"
						>
							Resume ↓
						</button>
					</div>
				{/each}
			</div>
		{/if}

		<!-- Available agents to launch -->
		{#if selectedAgents.length > 0}
			<div class="space-y-1.5">
				<p class="text-[10px] font-semibold uppercase tracking-wide text-slate-400">Available agents</p>
				{#each selectedAgents as agent (agent.id)}
					{@const agentStatus = agent.status ?? 'ready'}
					{@const isBlocked = agentStatus === 'blocked'}
					{@const isDone = agentStatus === 'completed'}
					{@const alreadyOpen = existingSessions.some((s) => s.agentId === agent.id)}
					{@const missingFiles = (agent.blocked_by ?? []).map((p) => p.split('/').pop() ?? p)}
					<div
						class="rounded-lg border px-3 py-2 space-y-1
						       {isBlocked
							       ? 'border-amber-200 bg-amber-50/50'
							       : isDone
							         ? 'border-emerald-200 bg-emerald-50/40'
							         : 'border-slate-200 bg-white'}"
					>
						<div class="flex items-center gap-2">
							<div class="flex-1 min-w-0">
								<span class="text-xs font-semibold {isBlocked ? 'text-amber-800' : isDone ? 'text-emerald-800' : 'text-slate-800'}">
									{agent.name || agent.id}
								</span>
								{#if agent.role}
									<span class="ml-2 text-[10px] text-slate-400">{agent.role}</span>
								{/if}
							</div>
							{#if alreadyOpen}
								<span class="text-[10px] text-slate-400 italic">already open</span>
							{:else if isBlocked}
								<span class="text-[10px] px-2 py-0.5 rounded-md bg-amber-100 text-amber-700 font-medium shrink-0">
									Blocked
								</span>
							{:else if isDone}
								<span class="text-[10px] text-emerald-600 font-medium shrink-0">✓ Done</span>
								<button
									onclick={() => launch(agent.id)}
									disabled={launching === agent.id}
									class="text-[11px] px-2.5 py-1 rounded-md font-medium transition-colors shrink-0
									       {launching === agent.id
										       ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
										       : 'border border-emerald-300 text-emerald-700 hover:bg-emerald-50'}"
								>
									{launching === agent.id ? 'Launching…' : '↻ Re-run'}
								</button>
							{:else}
								<button
									onclick={() => launch(agent.id)}
									disabled={launching === agent.id}
									class="text-[11px] px-2.5 py-1 rounded-md font-medium transition-colors shrink-0
									       {launching === agent.id
										       ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
										       : 'bg-slate-800 text-white hover:bg-slate-700'}"
								>
									{launching === agent.id ? 'Launching…' : 'Launch'}
								</button>
							{/if}
						</div>
						{#if isBlocked && missingFiles.length > 0}
							<p class="text-[10px] text-amber-700 leading-snug">
								Needs: {missingFiles.join(', ')}
							</p>
						{/if}
					</div>
				{/each}
			</div>
		{:else if existingSessions.length === 0}
			<p class="text-xs text-slate-400 italic">No agents available for this folder type.</p>
		{/if}

		<!-- Disambiguation picker -->
		{#if disambiguateCandidates}
			<div class="rounded-lg border border-amber-200 bg-amber-50 p-3 space-y-2">
				<p class="text-xs font-semibold text-amber-800">Multiple agents available — pick one:</p>
				<div class="space-y-1">
					{#each disambiguateCandidates as candidate (candidate.id)}
						{@const cStatus = candidate.status ?? 'ready'}
						<button
							onclick={() => launch(candidate.id)}
							disabled={!!launching}
							class="w-full text-left flex items-center gap-2 px-3 py-2 rounded-md border border-amber-200
							       bg-white hover:bg-amber-50 transition-colors text-xs"
						>
							<span class="font-semibold text-slate-800">{candidate.name || candidate.id}</span>
							{#if candidate.role}
								<span class="text-slate-400">{candidate.role}</span>
							{/if}
							{#if cStatus === 'completed'}
								<span class="ml-auto text-[10px] text-emerald-600 font-medium">✓ Done</span>
							{:else if cStatus === 'blocked'}
								<span class="ml-auto text-[10px] text-amber-600 font-medium">Blocked</span>
							{/if}
						</button>
					{/each}
				</div>
				<button
					onclick={() => { disambiguateCandidates = null; }}
					class="text-[10px] text-amber-600 hover:text-amber-800"
				>
					Cancel
				</button>
			</div>
		{/if}

		<!-- Error -->
		{#if launchError}
			<div class="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2">
				<p class="flex-1 text-xs text-red-700">{launchError}</p>
				<button
					onclick={() => (launchError = '')}
					class="shrink-0 text-red-400 hover:text-red-700 transition-colors text-sm leading-none mt-0.5"
					aria-label="Dismiss"
				>✕</button>
			</div>
		{/if}
	{/if}
</div>
