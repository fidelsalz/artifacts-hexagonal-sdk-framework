<script lang="ts">
	import { API_BASE } from '$lib/config';
	import { sessionStore } from '$lib/stores/sessionStore.svelte';
	import type { AgentCandidate, FileEntry, TreeNodeData } from '$lib/types';
	import { SvelteMap, SvelteSet } from 'svelte/reactivity';

	let {
		treeNode,
		campaign,
		onFolderSelect,
		onFileSelect,
		onRefresh,
	}: {
		treeNode: TreeNodeData;
		campaign: string;
		onFolderSelect: (path: string, agents: AgentCandidate[]) => void;
		onFileSelect: (path: string, parentNode: TreeNodeData) => void;
		onRefresh?: () => void;
	} = $props();

	// ---------- local state ----------
	// SvelteSet/SvelteMap are used so that .add()/.delete()/.set() mutations
	// are tracked by Svelte 5's reactivity system (plain Set/Map are not).
	const expandedPaths = new SvelteSet<string>();
	const fileEntries = new SvelteMap<string, FileEntry[]>();
	const loadingPaths = new SvelteSet<string>();
	const promoting = new SvelteSet<string>();
	const inferredAgentIds = new SvelteMap<string, string[]>();
	let selectedPath = $state('');

	// ---------- flat list derivation ----------
	type FlatItem =
		| { kind: 'folder'; node: TreeNodeData; depth: number }
		| { kind: 'file'; entry: FileEntry; depth: number; parentNode: TreeNodeData };

	function buildFlatList(node: TreeNodeData, depth: number): FlatItem[] {
		const items: FlatItem[] = [{ kind: 'folder', node, depth }];
		if (!expandedPaths.has(node.path)) return items;

		// Convention-named subfolders first (from tree data)
		for (const child of node.children) {
			items.push(...buildFlatList(child, depth + 1));
		}

		// Directories from lazy list not already covered by tree children
		const knownChildPaths = new Set(node.children.map((c) => c.path));
		const entries = fileEntries.get(node.path) ?? [];
		for (const d of entries.filter((e) => e.type === 'dir' && !knownChildPaths.has(e.path))) {
			const syntheticNode: TreeNodeData = {
				name: d.name,
				path: d.path,
				available_agents: inferredAgentIds.get(d.path) ?? [],
				children: [],
			};
			items.push(...buildFlatList(syntheticNode, depth + 1));
		}

		// Then files from lazy list — carry parentNode so clicks know which level they belong to
		for (const f of entries.filter((e) => e.type === 'file')) {
			items.push({ kind: 'file', entry: f, depth: depth + 1, parentNode: node });
		}

		return items;
	}

	const flatItems = $derived(buildFlatList(treeNode, 0));

	// ---------- helpers ----------
	function hasActiveSession(path: string): boolean {
		return sessionStore.sessions.some((s) => s.cwd === path);
	}

	async function loadFiles(path: string) {
		if (fileEntries.has(path) || loadingPaths.has(path)) return;
		loadingPaths.add(path);
		try {
			const res = await fetch(`${API_BASE}/api/files/list?path=${encodeURIComponent(path)}`);
			if (res.ok) {
				const data = await res.json();
				const entries = data.entries as FileEntry[];
				// Pre-fetch agents for dirs not yet known, so synthetic nodes render with correct agents
				await Promise.all(
					entries
						.filter((e) => e.type === 'dir' && !inferredAgentIds.has(e.path))
						.map(async (d) => {
							const r = await fetch(
								`${API_BASE}/api/infer-agent?path=${encodeURIComponent(d.path)}&campaign=${encodeURIComponent(campaign)}`
							);
							inferredAgentIds.set(
								d.path,
								r.ok ? ((await r.json()) as AgentCandidate[]).map((c) => c.id) : []
							);
						})
				);
				fileEntries.set(path, entries);
			}
		} finally {
			loadingPaths.delete(path);
		}
	}

	function toggleFolder(node: TreeNodeData) {
		selectedPath = node.path;
		if (expandedPaths.has(node.path)) {
			expandedPaths.delete(node.path);
		} else {
			expandedPaths.add(node.path);
			loadFiles(node.path);
		}
		// Build AgentCandidate list from available_agents strings
		const agents: AgentCandidate[] = node.available_agents.map((id) => ({
			id,
			name: id,
			role: '',
		}));
		onFolderSelect(node.path, agents);
	}

	function clickFile(entry: FileEntry, parentNode: TreeNodeData) {
		selectedPath = entry.path;
		onFileSelect(entry.path, parentNode);
	}

	function fileName(path: string): string {
		return path.split('/').pop() ?? path;
	}

	// ---------- INT hierarchy count badges ----------
	function countChildren(node: TreeNodeData, pattern: RegExp): number {
		return node.children.filter((c) => pattern.test(c.name)).length;
	}

	function intCounts(node: TreeNodeData): { a: number; r: number; h: number } | null {
		if (node.name !== 'INT') return null;
		const angles = node.children.filter((c) => /^A\d+$/.test(c.name));
		const a = angles.length;
		const r = angles.reduce((sum, angle) => sum + countChildren(angle, /^A\d+R\d+$/), 0);
		const h = angles.reduce(
			(sum, angle) =>
				sum +
				angle.children
					.filter((arc) => /^A\d+R\d+$/.test(arc.name))
					.reduce((s, arc) => s + countChildren(arc, /^A\d+R\d+H\d+$/), 0),
			0
		);
		return a > 0 || r > 0 || h > 0 ? { a, r, h } : null;
	}

	function angleCounts(node: TreeNodeData): number | null {
		if (!/^A\d+$/.test(node.name) || !node.path.includes('/INT/')) return null;
		const r = countChildren(node, /^A\d+R\d+$/);
		return r > 0 ? r : null;
	}

	function arcCounts(node: TreeNodeData): number | null {
		if (!/^A\d+R\d+$/.test(node.name) || !node.path.includes('/INT/')) return null;
		const h = countChildren(node, /^A\d+R\d+H\d+$/);
		return h > 0 ? h : null;
	}

	function isPromotableHook(node: TreeNodeData): boolean {
		return /^A\d{2}R\d{2}H\d{2}$/.test(node.name) && node.path.includes('/INT/');
	}

	async function promoteHook(node: TreeNodeData, e: MouseEvent) {
		e.stopPropagation();
		if (promoting.has(node.path)) return;
		promoting.add(node.path);
		try {
			const res = await fetch(`${API_BASE}/api/promote-hook`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ path: node.path, campaign }),
			});
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				console.error('promote-hook failed:', err);
				return;
			}
			await handleRefresh();
		} finally {
			promoting.delete(node.path);
		}
	}

	function isPromotableArc(node: TreeNodeData): boolean {
		return (
			/^A\d+R\d+$/.test(node.name) &&
			node.path.includes('/INT/') &&
			node.children.some((c) => /^A\d+R\d+H\d+$/.test(c.name))
		);
	}

	async function promoteArc(node: TreeNodeData, e: MouseEvent) {
		e.stopPropagation();
		if (promoting.has(node.path)) return;
		promoting.add(node.path);
		try {
			const res = await fetch(`${API_BASE}/api/promote-arc`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ path: node.path, platform: 'ML' }),
			});
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				console.error('promote-arc failed:', err);
				return;
			}
			await handleRefresh();
		} finally {
			promoting.delete(node.path);
		}
	}

	let refreshing = $state(false);

	async function handleRefresh() {
		refreshing = true;
		// Bust the file-list cache for every expanded folder so they re-fetch on next expand
		for (const path of expandedPaths) {
			fileEntries.delete(path);
		}
		// Re-fetch expanded folders immediately
		const reloads = [...expandedPaths].map((p) => loadFiles(p));
		await Promise.all(reloads);
		onRefresh?.();
		refreshing = false;
	}
</script>

<div class="py-2 text-sm">
	<!-- Refresh button -->
	<div class="px-3 pb-1 flex justify-end">
		<button
			onclick={handleRefresh}
			disabled={refreshing}
			title="Refresh tree"
			class="text-[10px] text-slate-400 hover:text-slate-600 disabled:opacity-40 transition-colors px-1 py-0.5 rounded"
		>
			{refreshing ? '⟳' : '↺'} refresh
		</button>
	</div>

	{#each flatItems as item (item.kind === 'folder' ? item.node.path : item.entry.path)}
		{#if item.kind === 'folder'}
			{@const node = item.node}
			{@const isExpanded = expandedPaths.has(node.path)}
			{@const isSelected = selectedPath === node.path}
			{@const isLoading = loadingPaths.has(node.path)}
			{@const hasSession = hasActiveSession(node.path)}
			{@const ic = intCounts(node)}
			{@const ac = angleCounts(node)}
			{@const hc = arcCounts(node)}
			<!-- svelte-ignore a11y_interactive_supports_focus -->
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<div
				role="button"
				onclick={() => toggleFolder(node)}
				class="flex items-center gap-1.5 rounded-md px-2 py-1.5 cursor-pointer transition-colors
				       {isSelected ? 'bg-emerald-50 text-emerald-800' : 'text-slate-700 hover:bg-slate-100'}"
				style="padding-left: {item.depth * 1.25 + 0.5}rem"
			>
				<span class="shrink-0 text-[10px] text-slate-400 w-3 text-center select-none">
					{isExpanded ? '▾' : '▸'}
				</span>
				<span class="shrink-0 text-[13px] select-none">{item.depth === 0 ? '📁' : '📂'}</span>
				<span class="flex-1 min-w-0 truncate font-medium text-xs">{node.name}</span>

				{#if ic}
					<span class="shrink-0 flex items-center gap-0.5 text-[10px] font-medium tabular-nums" title="Angles · Arcs · Hooks">
						<span class="text-violet-500">{ic.a}A</span>
						<span class="text-slate-300">·</span>
						<span class="text-amber-500">{ic.r}R</span>
						<span class="text-slate-300">·</span>
						<span class="text-emerald-500">{ic.h}H</span>
					</span>
				{/if}
				{#if ac !== null}
					<span class="shrink-0 text-[10px] text-amber-500 font-medium tabular-nums" title="Arcs">
						{ac}R
					</span>
				{/if}
				{#if hc !== null}
					<span class="shrink-0 text-[10px] text-emerald-500 font-medium tabular-nums" title="Hooks">
						{hc}H
					</span>
				{/if}

				{#if hasSession}
					<span class="shrink-0 w-1.5 h-1.5 rounded-full bg-emerald-500" title="Active session"></span>
				{/if}
				{#if isPromotableHook(node)}
					<button
						onclick={(e) => promoteHook(node, e)}
						disabled={promoting.has(node.path)}
						title="Promote to SCE"
						class="shrink-0 text-[10px] font-medium px-1.5 py-0.5 rounded
						       bg-emerald-50 text-emerald-700 hover:bg-emerald-100
						       disabled:opacity-40 transition-colors"
					>
						{promoting.has(node.path) ? '…' : '→ SCE'}
					</button>
				{/if}
				{#if isPromotableArc(node)}
					<button
						onclick={(e) => promoteArc(node, e)}
						disabled={promoting.has(node.path)}
						title="Promote to IMG"
						class="shrink-0 text-[10px] font-medium px-1.5 py-0.5 rounded
						       bg-sky-50 text-sky-700 hover:bg-sky-100
						       disabled:opacity-40 transition-colors"
					>
						{promoting.has(node.path) ? '…' : '→ IMG'}
					</button>
				{/if}
				{#if isLoading}
					<span class="shrink-0 text-[10px] text-slate-400 animate-pulse">…</span>
				{/if}

				{#if node.available_agents.length > 0}
					<span class="shrink-0 text-[10px] bg-slate-100 text-slate-500 rounded-full px-1.5 py-0.5 font-medium">
						{node.available_agents.length}
					</span>
				{/if}
			</div>

		{:else}
			{@const entry = item.entry}
			{@const isSelected = selectedPath === entry.path}
			<!-- svelte-ignore a11y_interactive_supports_focus -->
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<div
				role="button"
				onclick={() => clickFile(entry, item.parentNode)}
				class="flex items-center gap-1.5 rounded-md px-2 py-1 cursor-pointer transition-colors
				       {isSelected ? 'bg-slate-100 text-slate-900' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-700'}"
				style="padding-left: {item.depth * 1.25 + 0.5}rem"
			>
				<span class="shrink-0 text-[11px] select-none">📄</span>
				<span class="flex-1 min-w-0 truncate text-xs">{entry.name}</span>
			</div>
		{/if}
	{/each}
</div>
