<script lang="ts">
	import { page } from '$app/state';
	import { API_BASE } from '$lib/config';
	import AgentChatPanel from '$lib/components/AgentChatPanel.svelte';
	import AgentLauncher from '$lib/components/AgentLauncher.svelte';
	import CampaignTree from '$lib/components/CampaignTree.svelte';
	import FileViewer from '$lib/components/FileViewer.svelte';
	import { closeAllSessions, sessionStore } from '$lib/stores/sessionStore.svelte';
	import type { AgentCandidate, AgentStatus, CampaignData, TreeNodeData } from '$lib/types';
	import { onMount } from 'svelte';

	const slug = page.params.slug ?? '';

	let campaign = $state<CampaignData | null>(null);
	let treeNode = $state<TreeNodeData | null>(null);
	let selectedFolder = $state('');
	let selectedFolderAgents = $state<AgentCandidate[]>([]);
	let selectedFile = $state<string | null>(null);
	let loading = $state(true);
	let error = $state('');
	let confirming = $state(false);

	let fileSection = $state<HTMLElement | null>(null);
	let chatSection = $state<HTMLElement | null>(null);

	// Collapse state for each panel
	let treeOpen = $state(true);
	let fileOpen = $state(true);
	let agentsOpen = $state(true);
	let chatOpen = $state(true);

	// Sidebar resize
	let sidebarWidth = $state(260);
	let resizing = $state(false);

	function startResize(e: MouseEvent) {
		e.preventDefault();
		const startX = e.clientX;
		const startWidth = sidebarWidth;
		resizing = true;

		function onMove(ev: MouseEvent) {
			sidebarWidth = Math.max(160, Math.min(520, startWidth + ev.clientX - startX));
		}
		function onUp() {
			resizing = false;
			document.removeEventListener('mousemove', onMove);
			document.removeEventListener('mouseup', onUp);
		}
		document.addEventListener('mousemove', onMove);
		document.addEventListener('mouseup', onUp);
	}

	onMount(async () => {
		try {
			const [campaignRes, treeRes] = await Promise.all([
				fetch(`${API_BASE}/api/campaigns/${slug}`),
				fetch(`${API_BASE}/api/tree`),
			]);
			if (!campaignRes.ok) throw new Error(`Campaign not found (HTTP ${campaignRes.status})`);
			campaign = await campaignRes.json();

			const tree: TreeNodeData[] = await treeRes.json();
			treeNode = tree.find((n) => n.name === slug) ?? null;

			// Default selection: campaign root folder
			if (campaign && treeNode) {
				selectedFolder = campaign.path;
				selectedFolderAgents = normalizeAgents(treeNode.available_agents);
			}
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			loading = false;
		}
	});

	function handleFolderSelect(path: string, agents: AgentCandidate[]) {
		selectedFolder = path;
		selectedFolderAgents = agents;
		selectedFile = null;
	}

	function handleFileSelect(path: string, parentNode: TreeNodeData) {
		selectedFile = path;
		// Sync agents panel to the folder that owns this file
		selectedFolder = parentNode.path;
		selectedFolderAgents = normalizeAgents(parentNode.available_agents);
		fileSection?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	// Backend root node returns string[] for available_agents; children return TreeAgentRef[].
	// This normalizes both so AgentLauncher always gets consistent AgentCandidate objects.
	function normalizeAgents(raw: unknown[]): AgentCandidate[] {
		return raw.map((a) =>
			typeof a === 'string'
				? { id: a, name: a, role: '', status: 'ready' as AgentStatus, blocked_by: [] }
				: {
						id: (a as { id: string }).id,
						name: (a as { id: string }).id,
						role: '',
						status: (a as { status: AgentStatus }).status ?? 'ready',
						blocked_by: (a as { blocked_by: string[] }).blocked_by ?? [],
					}
		);
	}

	function handleSessionLaunched(_key: string) {
		chatSection?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	async function refreshTree() {
		try {
			const res = await fetch(`${API_BASE}/api/tree`);
			if (!res.ok) return;
			const tree: TreeNodeData[] = await res.json();
			treeNode = tree.find((n) => n.name === slug) ?? treeNode;
		} catch {
			// silently ignore — tree stays as-is
		}
	}

	function confirmClose() {
		closeAllSessions();
		window.close();
	}

	function formatDate(iso: string) {
		return new Date(iso).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric',
		});
	}
</script>

<div class="h-screen flex flex-col overflow-hidden bg-white" class:select-none={resizing}>

	<!-- Top bar -->
	<header class="shrink-0 border-b border-slate-200/60 px-5 py-3 flex items-center gap-3">
		<button
			onclick={() => (treeOpen = !treeOpen)}
			title={treeOpen ? 'Collapse tree' : 'Expand tree'}
			class="shrink-0 text-slate-400 hover:text-slate-700 transition-colors text-sm leading-none w-6 h-6 flex items-center justify-center rounded hover:bg-slate-100"
		>{treeOpen ? '◀' : '▶'}</button>
		{#if campaign}
			<div class="flex items-center gap-2 min-w-0 flex-1">
				<span class="font-semibold text-slate-900 text-sm truncate">{campaign.name}</span>
				<span class="bg-slate-100 text-slate-600 text-xs font-semibold rounded-full px-2 py-0.5 shrink-0">{campaign.slug}</span>
				<span class="text-xs text-slate-400 shrink-0 hidden sm:inline">{formatDate(campaign.created_at)}</span>
			</div>
		{:else}
			<div class="flex-1"></div>
		{/if}
		{#if sessionStore.sessions.length > 0}
			<span class="text-[11px] text-emerald-600 font-medium shrink-0">
				{sessionStore.sessions.length} session{sessionStore.sessions.length !== 1 ? 's' : ''} open
			</span>
		{/if}
		<button
			onclick={() => (confirming = true)}
			class="shrink-0 text-xs font-medium px-3 py-1.5 rounded-lg border border-slate-300 text-slate-600
			       hover:bg-red-50 hover:border-red-300 hover:text-red-700 transition-colors"
		>
			Close campaign
		</button>
	</header>

	<!-- Confirmation overlay -->
	{#if confirming}
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div
			class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
			onclick={() => (confirming = false)}
		>
			<div
				class="bg-white rounded-xl border border-slate-200 shadow-xl p-6 w-80 space-y-4"
				onclick={(e) => e.stopPropagation()}
				role="dialog"
				aria-modal="true"
				tabindex="-1"
			>
				<div>
					<p class="text-sm font-semibold text-slate-900">Close this campaign?</p>
					<p class="text-xs text-slate-500 mt-1">
						All running agents will be stopped and this tab will close.
						Agent output already written to disk is preserved.
					</p>
				</div>
				<div class="flex gap-2 justify-end">
					<button
						onclick={() => (confirming = false)}
						class="text-xs font-medium px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors"
					>
						Cancel
					</button>
					<button
						onclick={confirmClose}
						class="text-xs font-medium px-3 py-1.5 rounded-lg bg-red-600 text-white hover:bg-red-500 transition-colors"
					>
						Close tab
					</button>
				</div>
			</div>
		</div>
	{/if}

	{#if loading}
		<div class="flex-1 flex items-center justify-center">
			<p class="text-sm text-slate-400 animate-pulse">Loading campaign…</p>
		</div>
	{:else if error}
		<div class="flex-1 flex items-center justify-center">
			<p class="text-sm text-red-600">{error}</p>
		</div>
	{:else if campaign && treeNode}
		<div class="flex-1 flex min-h-0">

			<!-- Left sidebar: campaign tree (CSS width collapse + drag resize) -->
			<aside
				style="width: {treeOpen ? sidebarWidth : 0}px"
				class="relative shrink-0 border-r border-slate-200 overflow-y-auto overflow-x-hidden bg-slate-50/50
				       {resizing ? '' : 'transition-[width] duration-200'}"
			>
				<div style="width: {sidebarWidth}px; padding-right: 10px">
					<div class="px-3 pt-3 pb-1">
						<p class="text-[10px] font-semibold uppercase tracking-wide text-slate-400">Campaign tree</p>
					</div>
					<CampaignTree
						{treeNode}
						campaign={slug}
						onFolderSelect={handleFolderSelect}
						onFileSelect={handleFileSelect}
						onRefresh={refreshTree}
					/>
				</div>

				<!-- Drag handle on the right edge -->
				{#if treeOpen}
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<div
						onmousedown={startResize}
						class="absolute top-0 right-0 bottom-0 w-1 cursor-col-resize
						       hover:bg-slate-300 {resizing ? 'bg-slate-300' : ''} transition-colors"
					></div>
				{/if}
			</aside>

			<!-- Right: three sections (block scroll, not flex-col) -->
			<main class="flex-1 overflow-y-auto">

				<!-- Section 1: File viewer -->
				<section bind:this={fileSection} class="border-b border-slate-200">
					<!-- svelte-ignore a11y_interactive_supports_focus -->
					<!-- svelte-ignore a11y_click_events_have_key_events -->
					<div
						role="button"
						onclick={() => (fileOpen = !fileOpen)}
						class="flex items-center justify-between px-6 py-3 cursor-pointer select-none hover:bg-slate-50 transition-colors"
					>
						<p class="text-[10px] font-semibold uppercase tracking-wide text-slate-400">File</p>
						<span class="text-[10px] text-slate-400">{fileOpen ? '▾' : '▸'}</span>
					</div>
					{#if fileOpen}
						<div class="px-6 pb-4">
							<FileViewer filePath={selectedFile} />
						</div>
					{/if}
				</section>

				<!-- Section 2: Agent launcher -->
				<section class="border-b border-slate-200">
					<!-- svelte-ignore a11y_interactive_supports_focus -->
					<!-- svelte-ignore a11y_click_events_have_key_events -->
					<div
						role="button"
						onclick={() => (agentsOpen = !agentsOpen)}
						class="flex items-center justify-between px-6 py-3 cursor-pointer select-none hover:bg-slate-50 transition-colors"
					>
						<p class="text-[10px] font-semibold uppercase tracking-wide text-slate-400">Agents</p>
						<span class="text-[10px] text-slate-400">{agentsOpen ? '▾' : '▸'}</span>
					</div>
					{#if agentsOpen}
						<div class="px-6 pb-4">
							<AgentLauncher
								selectedPath={selectedFolder}
								selectedAgents={selectedFolderAgents}
								campaign={slug}
								onSessionLaunched={handleSessionLaunched}
							/>
						</div>
					{/if}
				</section>

				<!-- Section 3: Agent chat panels (always mounted) -->
				<section bind:this={chatSection} class="border-b border-slate-200">
					<!-- svelte-ignore a11y_interactive_supports_focus -->
					<!-- svelte-ignore a11y_click_events_have_key_events -->
					<div
						role="button"
						onclick={() => (chatOpen = !chatOpen)}
						class="flex items-center justify-between px-6 py-3 cursor-pointer select-none hover:bg-slate-50 transition-colors"
					>
						<p class="text-[10px] font-semibold uppercase tracking-wide text-slate-400">
							Agent chat
							{#if sessionStore.sessions.length > 0}
								<span class="ml-1 normal-case font-normal text-emerald-600">({sessionStore.sessions.length})</span>
							{/if}
						</p>
						<span class="text-[10px] text-slate-400">{chatOpen ? '▾' : '▸'}</span>
					</div>
					<div class="px-6 pb-4 {chatOpen ? '' : 'hidden'}">
						{#if sessionStore.sessions.length === 0 && chatOpen}
							<p class="text-xs text-slate-400 italic">Launch an agent above to start a session.</p>
						{/if}
						{#each sessionStore.sessions as session (session.key)}
							<div class={session.key === sessionStore.activeKey ? '' : 'hidden'}>
								<AgentChatPanel sessionKey={session.key} />
							</div>
						{/each}
					</div>
				</section>

			</main>
		</div>
	{/if}

</div>
