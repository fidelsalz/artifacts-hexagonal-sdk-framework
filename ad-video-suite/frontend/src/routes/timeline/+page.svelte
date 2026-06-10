<script lang="ts">
	import { API_BASE } from '$lib/config';
	import AppNav from '$lib/components/AppNav.svelte';
	import FileViewer from '$lib/components/FileViewer.svelte';
	import type { CampaignData, TreeNodeData } from '$lib/types';
	import { SvelteMap } from 'svelte/reactivity';
	import { onMount } from 'svelte';

	// ── Types ──────────────────────────────────────────────────────────────────
	type TrackItem = {
		id: string;
		start_s: number;
		end_s: number;
		label: string;
		[key: string]: unknown;
	};

	type ShotApprovedFrame = {
		attempt: string;
		model: string;
		first_frame_job_id: string | null;
		last_frame_job_id: string | null;
		character_reference_job_id: string | null;
		first_frame?: string | null;
		last_frame?: string | null;
	};

	type ShotFiles = {
		image_generation?: { approved: ShotApprovedFrame[]; attempts_count: number };
		video_url?: string | null;
	};

	type CharacterAsset = {
		available: boolean;
		higgsfield_job_id?: string | null;
		generation_prompt?: string;
		approved_image?: string | null;
		character_json?: string | null;
	};

	type ProductAsset = { available: boolean; files: string[] };

	type TimelineAssets = {
		character?: CharacterAsset;
		product?: ProductAsset;
		[key: string]: unknown;
	};

	type TimelineTrack = { available: boolean; items: TrackItem[] };

	type TimelineData = {
		cwd: string;
		total_duration_s: number;
		tracks: Record<string, TimelineTrack>;
		assets: TimelineAssets;
	};

	type SelectedSlot = { trackKey: string; item: TrackItem };

	type ImgAdsConcept = {
		id: number;
		concept: string;
		hook?: string;
		status: string;
		image?: string | null;
		headline_ptbr?: string;
		[key: string]: unknown;
	};

	type ImgAdsData = {
		cwd: string;
		platform: string;
		concepts: ImgAdsConcept[];
		assets: TimelineAssets;
	};

	// ── Layout state ──────────────────────────────────────────────────────────
	let sidebarOpen = $state(true);
	// ── Campaign / selector state ──────────────────────────────────────────────
	let campaigns = $state<CampaignData[]>([]);
	let loadingCampaigns = $state(true);
	let campaignsError = $state('');

	let selectedCampaign = $state('');
	let selectedAngle = $state('');
	let selectedArc = $state('');
	let selectedHook = $state('');
	let campaignTree = $state<TreeNodeData | null>(null);
	let loadingTree = $state(false);

	// ── Timeline state ─────────────────────────────────────────────────────────
	let timelineData = $state<TimelineData | null>(null);
	let loadingTimeline = $state(false);
	let timelineError = $state('');
	let selectedSlot = $state<SelectedSlot | null>(null);
	let selectedAssetPath = $state<string | null>(null);
	let imgAdsData = $state<ImgAdsData | null>(null);

	// ── Detail panel drag state ───────────────────────────────────────────────
	let detailHeight = $state(288);
	let detailDragging = $state(false);
	let detailDragStartY = 0;
	let detailDragStartH = 0;

	// Frame images cache: shotId → array of local approved image paths
	const frameImageCache = new SvelteMap<string, string[]>();

	// ── Descriptions cache ────────────────────────────────────────────────────
	const descriptions = new SvelteMap<string, string>();

	async function loadDesc(filePath: string) {
		if (descriptions.has(filePath)) return;
		descriptions.set(filePath, '');
		try {
			const res = await fetch(`${API_BASE}/api/files/read?path=${encodeURIComponent(filePath)}`);
			if (!res.ok) return;
			const data = await res.json();
			const first = (data.content as string)
				.split('\n')
				.map((l: string) => l.replace(/^#+\s*/, '').trim())
				.find((l: string) => l.length > 0) ?? '';
			descriptions.set(filePath, first);
		} catch {
			// leave empty on error
		}
	}

	// ── Derived: INT hierarchy ────────────────────────────────────────────────
	const intNode = $derived(campaignTree?.children.find((c) => c.name === 'INT') ?? null);
	const angles = $derived(intNode?.children.filter((c) => /^A\d+$/.test(c.name)) ?? []);
	const angleNode = $derived(angles.find((a) => a.name === selectedAngle) ?? null);
	const arcs = $derived(angleNode?.children.filter((c) => /^A\d+R\d+$/.test(c.name)) ?? []);
	const arcNode = $derived(arcs.find((a) => a.name === selectedArc) ?? null);
	const hooks = $derived(arcNode?.children.filter((c) => /^A\d+R\d+H\d+$/.test(c.name)) ?? []);

	// ── Derived: promoted hooks from SCE tree ─────────────────────────────────
	const sceNode = $derived(campaignTree?.children.find((c) => c.name === 'SCE') ?? null);
	const promotedHooks = $derived(new Set(sceNode?.children.map((c) => c.name) ?? []));

	// ── Derived: IMG node ─────────────────────────────────────────────────────
	const imgNode = $derived(campaignTree?.children.find((c) => c.name === 'IMG') ?? null);

	// Auto-load img-ads when arc changes — construct path directly so the effect
	// tracks selectedArc and campaignTree as dependencies (not an intermediate
	// derived that stays null and prevents re-firing).
	$effect(() => {
		if (!selectedArc || !campaignTree) { imgAdsData = null; return; }
		const platformName = imgNode?.children[0]?.name ?? 'ML';
		loadImgAds(`${campaignTree.path}/IMG/${platformName}/${selectedArc}`);
	});

	function arcLeadsToPromotion(arc: TreeNodeData): boolean {
		return arc.children.some((c) => /^A\d+R\d+H\d+$/.test(c.name) && promotedHooks.has(c.name));
	}

	function angleLeadsToPromotion(angle: TreeNodeData): boolean {
		return angle.children
			.filter((c) => /^A\d+R\d+$/.test(c.name))
			.some((arc) => arcLeadsToPromotion(arc));
	}

	// ── Lazy-load descriptions when lists become visible ──────────────────────
	$effect(() => {
		for (const a of angles) loadDesc(`${a.path}/${a.name}.md`);
	});
	$effect(() => {
		for (const r of arcs) loadDesc(`${r.path}/${r.name}.md`);
	});
	$effect(() => {
		for (const h of hooks) loadDesc(`${h.path}/${h.name}.md`);
	});

	// ── Derived: SCE cwd ──────────────────────────────────────────────────────
	const hookCwd = $derived(
		selectedHook && campaignTree ? `${campaignTree.path}/SCE/${selectedHook}` : ''
	);

	// ── Derived: path to show in the FileViewer ──────────────────────────────
	// Asset clicks take priority; for shot slots show video_url if generated.
	const viewerPath = $derived.by((): string | null => {
		if (selectedAssetPath) return selectedAssetPath;
		if (!selectedSlot) return null;
		const files = selectedSlot.item.files as ShotFiles | undefined;
		return files?.video_url ?? null;
	});

	// ── Ad image carousel ─────────────────────────────────────────────────────
	const adImageConcepts = $derived(
		(imgAdsData?.concepts ?? []).filter((c): c is ImgAdsConcept & { image: string } => c.image != null)
	);
	const selectedConceptIdx = $derived(
		adImageConcepts.findIndex((c) => c.image === selectedAssetPath)
	);
	const isAdImage = $derived(selectedConceptIdx !== -1);

	function prevConcept() {
		const n = adImageConcepts.length;
		selectAsset(adImageConcepts[(selectedConceptIdx - 1 + n) % n].image);
	}
	function nextConcept() {
		selectAsset(adImageConcepts[(selectedConceptIdx + 1) % adImageConcepts.length].image);
	}

	// ── Track definitions ─────────────────────────────────────────────────────
	const TRACKS = [
		{ key: 'script',      label: 'Script',     rowBg: 'bg-blue-50/60',    pill: 'bg-blue-100 text-blue-800 border border-blue-200',       ring: 'ring-2 ring-blue-400' },
		{ key: 'storyboard',  label: 'Storyboard', rowBg: 'bg-violet-50/60',  pill: 'bg-violet-100 text-violet-800 border border-violet-200', ring: 'ring-2 ring-violet-400' },
		{ key: 'scene_specs', label: 'Scene',      rowBg: 'bg-amber-50/60',   pill: 'bg-amber-100 text-amber-800 border border-amber-200',    ring: 'ring-2 ring-amber-400' },
		{ key: 'shots',       label: 'Shots',      rowBg: 'bg-emerald-50/60', pill: 'bg-emerald-100 text-emerald-800 border border-emerald-200', ring: 'ring-2 ring-emerald-400' },
		{ key: 'graphics',    label: 'Graphics',   rowBg: 'bg-rose-50/60',    pill: 'bg-rose-100 text-rose-800 border border-rose-200',       ring: 'ring-2 ring-rose-400' },
	] as const;

	const GEN_STATUS: Record<string, string> = {
		pending:        'bg-slate-200 text-slate-500',
		prompted:       'bg-yellow-100 text-yellow-700',
		imaged:         'bg-green-100 text-green-700',
		video_prompted: 'bg-sky-100 text-sky-700',
		generated:      'bg-emerald-100 text-emerald-700',
	};

	// ── Helpers ────────────────────────────────────────────────────────────────
	function slotStyle(start_s: number, end_s: number, total: number): string {
		const l = (start_s / total) * 100;
		const w = Math.max(((end_s - start_s) / total) * 100, 2);
		return `left:${l.toFixed(2)}%;width:${w.toFixed(2)}%;`;
	}

	function rulerTicks(total: number) {
		const step = total <= 40 ? 5 : 10;
		const out: { t: number; pct: string }[] = [];
		for (let t = 0; t <= total; t += step) {
			out.push({ t, pct: `${((t / total) * 100).toFixed(2)}%` });
		}
		return out;
	}

	function extraFields(item: TrackItem): { k: string; v: string }[] {
		const skip = new Set(['id', 'start_s', 'end_s', 'label', 'files']);
		return Object.entries(item)
			.filter(([k]) => !skip.has(k) && item[k] != null)
			.map(([k, v]) => ({ k, v: String(v) }));
	}

	function isSelected(trackKey: string, itemId: string): boolean {
		return selectedSlot?.trackKey === trackKey && selectedSlot.item.id === itemId;
	}

	function selectSlot(trackKey: string, item: TrackItem) {
		selectedSlot = isSelected(trackKey, item.id) ? null : { trackKey, item };
		selectedAssetPath = null;
	}

	function selectAsset(path: string) {
		selectedAssetPath = selectedAssetPath === path ? null : path;
		selectedSlot = null;
	}

	// ── Data loading ───────────────────────────────────────────────────────────
	async function loadCampaigns() {
		loadingCampaigns = true;
		campaignsError = '';
		try {
			const res = await fetch(`${API_BASE}/api/campaigns`);
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			campaigns = await res.json();
		} catch (e) {
			campaignsError = e instanceof Error ? e.message : String(e);
		} finally {
			loadingCampaigns = false;
		}
	}

	async function pickCampaign(slug: string) {
		selectedCampaign = slug;
		selectedAngle = ''; selectedArc = ''; selectedHook = '';
		timelineData = null; timelineError = ''; selectedSlot = null; campaignTree = null;
		if (!slug) return;
		loadingTree = true;
		try {
			const res = await fetch(`${API_BASE}/api/tree`);
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			const tree: TreeNodeData[] = await res.json();
			campaignTree = tree.find((n) => n.name === slug) ?? null;
		} finally {
			loadingTree = false;
		}
	}

	function pickAngle(name: string) {
		selectedAngle = name; selectedArc = ''; selectedHook = '';
		timelineData = null; timelineError = ''; selectedSlot = null; imgAdsData = null;
	}

	function pickArc(name: string) {
		selectedArc = name; selectedHook = '';
		timelineData = null; timelineError = ''; selectedSlot = null; imgAdsData = null;
	}

	function pickHook(name: string) {
		selectedHook = selectedHook === name ? '' : name;
		timelineData = null; timelineError = ''; selectedSlot = null;
	}

	async function loadImgAds(cwd: string) {
		try {
			const res = await fetch(`${API_BASE}/api/img-ads?cwd=${encodeURIComponent(cwd)}`);
			imgAdsData = res.ok ? await res.json() : null;
		} catch {
			imgAdsData = null;
		}
	}

	async function loadTimeline() {
		if (!hookCwd) return;
		loadingTimeline = true; timelineError = ''; timelineData = null; selectedSlot = null; selectedAssetPath = null;
		try {
			const res = await fetch(`${API_BASE}/api/timeline?cwd=${encodeURIComponent(hookCwd)}`);
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			timelineData = await res.json();
		} catch (e) {
			timelineError = e instanceof Error ? e.message : String(e);
		} finally {
			loadingTimeline = false;
		}
	}

	// Document-level drag handlers for the detail panel resize (mouse + touch)
	$effect(() => {
		function onMove(e: MouseEvent) {
			if (!detailDragging) return;
			const delta = detailDragStartY - e.clientY;
			detailHeight = Math.max(80, Math.min(detailDragStartH + delta, window.innerHeight - 160));
		}
		function onTouchMove(e: TouchEvent) {
			if (!detailDragging) return;
			const delta = detailDragStartY - e.touches[0].clientY;
			detailHeight = Math.max(80, Math.min(detailDragStartH + delta, window.innerHeight - 160));
		}
		function onUp() { detailDragging = false; }
		document.addEventListener('mousemove', onMove);
		document.addEventListener('mouseup', onUp);
		document.addEventListener('touchmove', onTouchMove, { passive: true });
		document.addEventListener('touchend', onUp);
		return () => {
			document.removeEventListener('mousemove', onMove);
			document.removeEventListener('mouseup', onUp);
			document.removeEventListener('touchmove', onTouchMove);
			document.removeEventListener('touchend', onUp);
		};
	});

	onMount(loadCampaigns);
</script>

<div class="h-screen flex flex-col bg-white overflow-hidden">
	<AppNav />

	<div class="flex flex-1 min-h-0">

		<!-- ── Left selector sidebar (CSS-collapsible) ───────────────────────── -->
		<aside
			style="width:{sidebarOpen ? 224 : 0}px"
			class="shrink-0 border-r border-slate-200 bg-slate-50/40 flex flex-col overflow-hidden transition-[width] duration-200"
		>
			<!-- inner fixed-width so content doesn't reflow during animation -->
			<div class="w-56 flex flex-col h-full">

				<div class="flex-1 overflow-y-auto px-3 pt-4 pb-2 space-y-5">

					<!-- Campaign -->
					<section>
						<p class="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-1.5">Campaign</p>
						{#if loadingCampaigns}
							<p class="text-xs text-slate-400 animate-pulse">Loading…</p>
						{:else if campaignsError}
							<p class="text-xs text-red-500">{campaignsError}</p>
						{:else if campaigns.length === 0}
							<p class="text-xs text-slate-400 italic">No campaigns.</p>
						{:else}
							<div class="space-y-0.5">
								{#each campaigns as c}
									<button onclick={() => pickCampaign(c.slug)}
										class="w-full text-left px-2.5 py-0.5 rounded-lg text-xs transition-colors border
										       {selectedCampaign === c.slug
											       ? 'bg-slate-900 text-white border-slate-900'
											       : 'text-slate-700 hover:bg-slate-100 border-transparent'}">
										<span class="font-mono text-[9px] opacity-60 mr-1">{c.slug}</span>{c.name}
									</button>
								{/each}
							</div>
						{/if}
					</section>

					<!-- Angle -->
					{#if selectedCampaign}
						<section>
							<p class="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-1.5">Angle</p>
							{#if loadingTree}
								<p class="text-xs text-slate-400 animate-pulse">Loading…</p>
							{:else if !intNode || angles.length === 0}
								<p class="text-xs text-slate-400 italic">No angles yet.</p>
							{:else}
								{@const reachableAngles = angles.filter((a) => angleLeadsToPromotion(a))}
								{@const blockedAngles = angles.filter((a) => !angleLeadsToPromotion(a))}
								<div class="space-y-0.5">
									{#each reachableAngles as a}
										{@const desc = descriptions.get(`${a.path}/${a.name}.md`) ?? ''}
										<button onclick={() => pickAngle(a.name)}
											class="w-full text-left px-2.5 py-0.5 rounded-lg text-xs transition-colors border
											       {selectedAngle === a.name
												       ? 'bg-violet-600 text-white border-violet-600'
												       : 'text-slate-700 hover:bg-slate-100 border-transparent'}">
											<span class="font-mono font-bold">{a.name}</span>
											{#if desc}
												<p class="text-[10px] leading-tight truncate
												          {selectedAngle === a.name ? 'opacity-80' : 'text-slate-400'}">{desc}</p>
											{/if}
										</button>
									{/each}
								</div>
								{#if blockedAngles.length > 0}
									<p class="text-[10px] text-slate-500 px-1 pt-1 leading-relaxed">
										{blockedAngles.map((a) => a.name).join(', ')} <span class="opacity-60">(blocked)</span>
									</p>
								{/if}
							{/if}
						</section>
					{/if}

					<!-- Arc -->
					{#if selectedAngle}
						<section>
							<p class="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-1.5">Arc</p>
							{#if arcs.length === 0}
								<p class="text-xs text-slate-400 italic">No arcs yet.</p>
							{:else}
								{@const reachableArcs = arcs.filter((r) => arcLeadsToPromotion(r))}
								{@const blockedArcs = arcs.filter((r) => !arcLeadsToPromotion(r))}
								<div class="space-y-0.5">
									{#each reachableArcs as r}
										{@const desc = descriptions.get(`${r.path}/${r.name}.md`) ?? ''}
										<button onclick={() => pickArc(r.name)}
											class="w-full text-left px-2.5 py-0.5 rounded-lg text-xs transition-colors border
											       {selectedArc === r.name
												       ? 'bg-amber-500 text-white border-amber-500'
												       : 'text-slate-700 hover:bg-slate-100 border-transparent'}">
											<span class="font-mono font-bold">{r.name}</span>
											{#if desc}
												<p class="text-[10px] leading-tight truncate
												          {selectedArc === r.name ? 'opacity-80' : 'text-slate-400'}">{desc}</p>
											{/if}
										</button>
									{/each}
								</div>
								{#if blockedArcs.length > 0}
									<p class="text-[10px] text-slate-500 px-1 pt-1 leading-relaxed">
										{blockedArcs.map((r) => r.name).join(', ')} <span class="opacity-60">(blocked)</span>
									</p>
								{/if}
							{/if}
						</section>
					{/if}

					<!-- Hook -->
					{#if selectedArc}
						<section>
							<p class="text-[10px] font-semibold uppercase tracking-wide text-slate-400 mb-1.5">Hook</p>
							{#if hooks.length === 0}
								<p class="text-xs text-slate-400 italic">No hooks yet.</p>
							{:else}
								{@const promotedHooks_ = hooks.filter((h) => promotedHooks.has(h.name))}
								{@const unpromotedHooks = hooks.filter((h) => !promotedHooks.has(h.name))}
								<div class="space-y-0.5">
									{#each promotedHooks_ as h}
										{@const desc = descriptions.get(`${h.path}/${h.name}.md`) ?? ''}
										<button onclick={() => pickHook(h.name)}
											class="w-full text-left px-2.5 py-0.5 rounded-lg text-xs transition-colors border
											       {selectedHook === h.name
												       ? 'bg-sky-500 text-white border-sky-500'
												       : 'text-slate-700 hover:bg-slate-100 border-transparent'}">
											<span class="font-mono font-bold">{h.name}</span>
											{#if desc}
												<p class="text-[10px] leading-tight truncate
												          {selectedHook === h.name ? 'opacity-80' : 'text-slate-400'}">{desc}</p>
											{/if}
										</button>
									{/each}
								</div>
								{#if unpromotedHooks.length > 0}
									<p class="text-[10px] text-slate-500 px-1 pt-1 leading-relaxed">
										{unpromotedHooks.map((h) => h.name).join(', ')} <span class="opacity-60">(not promoted)</span>
									</p>
								{/if}
							{/if}
						</section>
					{/if}

				</div>

				<!-- Pinned footer -->
				<div class="shrink-0 px-3 py-3 border-t border-slate-100">
					<button
						onclick={loadTimeline}
						disabled={loadingTimeline || !hookCwd}
						class="w-full bg-emerald-600 text-white text-xs font-semibold px-3 py-2.5 rounded-lg
						       hover:bg-emerald-500 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
					>
						{loadingTimeline ? 'Loading…' : 'Load timeline'}
					</button>
				</div>

			</div>
		</aside>

		<!-- ── Right: header + timeline + detail ─────────────────────────────── -->
		<div class="flex-1 flex flex-col min-h-0">

			<!-- Fixed header bar -->
			<div class="shrink-0 h-11 flex items-center gap-3 px-3 border-b border-slate-100 bg-white">
				<!-- Sidebar toggle -->
				<button
					onclick={() => (sidebarOpen = !sidebarOpen)}
					title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
					class="shrink-0 text-slate-400 hover:text-slate-700 transition-colors text-sm w-6 h-6
					       flex items-center justify-center rounded hover:bg-slate-100"
				>
					{sidebarOpen ? '◀' : '▶'}
				</button>

				<!-- Breadcrumb -->
				<div class="flex-1 flex items-center gap-1.5 text-[11px] min-w-0 flex-wrap">
					{#if selectedCampaign}
						<span class="bg-slate-100 text-slate-700 font-semibold px-2 py-0.5 rounded-full shrink-0">{selectedCampaign}</span>
					{/if}
					{#if selectedAngle}
						<span class="text-slate-300">›</span>
						<span class="bg-violet-100 text-violet-700 font-semibold px-2 py-0.5 rounded-full shrink-0">{selectedAngle}</span>
					{/if}
					{#if selectedArc}
						<span class="text-slate-300">›</span>
						<span class="bg-amber-100 text-amber-700 font-semibold px-2 py-0.5 rounded-full shrink-0">{selectedArc}</span>
					{/if}
					{#if selectedHook}
						<span class="text-slate-300">›</span>
						<span class="bg-sky-100 text-sky-700 font-semibold px-2 py-0.5 rounded-full shrink-0">{selectedHook}</span>
					{/if}
					{#if !selectedCampaign}
						<span class="text-slate-400 italic">Select a campaign to begin.</span>
					{/if}
				</div>

				<!-- Duration + refresh -->
				<div class="flex items-center gap-2 shrink-0">
					{#if timelineData}
						<span class="text-[10px] font-mono text-slate-400">{timelineData.total_duration_s}s</span>
					{/if}
					{#if hookCwd}
						<button
							onclick={loadTimeline}
							disabled={loadingTimeline}
							title="Refresh"
							class="text-[10px] text-slate-400 hover:text-slate-700 disabled:opacity-40 transition-colors
							       px-1.5 py-0.5 rounded hover:bg-slate-100"
						>{loadingTimeline ? '⟳' : '↺'}</button>
					{/if}
				</div>
			</div>

			<!-- Scrollable timeline area -->
			<div class="flex-1 min-h-0 overflow-auto bg-white">

				{#if timelineError}
					<div class="m-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
						{timelineError}
					</div>

				{:else if loadingTimeline}
					<div class="flex items-center justify-center h-40">
						<p class="text-sm text-slate-400 animate-pulse">Loading timeline…</p>
					</div>

				{:else if timelineData}
					<div class="min-w-[720px]">
						<!-- Time ruler -->
						<div class="flex border-b border-slate-200 bg-slate-50">
							<div class="w-24 shrink-0 border-r border-slate-200"></div>
							<div class="flex-1 relative h-7">
								{#each rulerTicks(timelineData.total_duration_s) as tick}
									<div
										class="absolute top-0 bottom-0 flex flex-col items-center"
										style="left:{tick.pct};transform:translateX(-50%)"
									>
										<span class="text-[9px] font-mono text-slate-400 leading-none pt-1">{tick.t}s</span>
										<div class="w-px flex-1 bg-slate-200 mt-0.5"></div>
									</div>
								{/each}
							</div>
						</div>

						<!-- Track rows -->
						{#each TRACKS as track}
							{@const tdata = timelineData.tracks[track.key]}
							<div class="flex border-b border-slate-100 last:border-b-0">
								<div class="w-24 shrink-0 border-r border-slate-100 flex items-center justify-end pr-3">
									<span class="text-[9px] font-semibold uppercase tracking-wide text-slate-400">{track.label}</span>
								</div>
								<div class="flex-1 relative h-12 {track.rowBg}">
									{#if tdata?.available && tdata.items.length > 0}
										{#each tdata.items as item}
											{@const sel = isSelected(track.key, item.id)}
											{@const genStatus = track.key === 'shots' ? (item.gen_status as string | undefined) : undefined}
											<button
												onclick={() => selectSlot(track.key, item)}
												title="{item.id}: {item.label}"
												style="position:absolute;top:4px;bottom:4px;{slotStyle(item.start_s, item.end_s, timelineData.total_duration_s)}"
												class="flex flex-col justify-center px-1.5 rounded overflow-hidden text-left
												       transition-all cursor-pointer {track.pill} {sel ? track.ring : 'hover:brightness-95'}"
											>
												<span class="text-[9px] font-bold opacity-60 leading-none">{item.id}</span>
												<span class="text-[10px] truncate leading-tight mt-0.5">{item.label}</span>
												{#if genStatus}
													<span class="text-[8px] leading-none mt-0.5 font-medium opacity-70">{genStatus}</span>
												{/if}
											</button>
										{/each}
									{:else if tdata && !tdata.available}
										<div class="absolute inset-0 flex items-center px-3">
											<span class="text-[9px] text-slate-300 italic">not generated</span>
										</div>
									{/if}
								</div>
							</div>
						{/each}

						<!-- Frames lane: first/last frame thumbnails from shots with approved image generation -->
						{#if timelineData.tracks.shots?.available}
							{@const shotsWithFrames = timelineData.tracks.shots.items.filter(s =>
								((s.files as ShotFiles)?.image_generation?.approved?.length ?? 0) > 0
							)}
							{#if shotsWithFrames.length > 0}
								<div class="flex border-b border-slate-100">
									<div class="w-24 shrink-0 border-r border-slate-100 flex items-center justify-end pr-3">
										<span class="text-[9px] font-semibold uppercase tracking-wide text-slate-400">Frames</span>
									</div>
									<div class="flex-1 relative h-16 bg-fuchsia-50/30">
										{#each shotsWithFrames as shot}
											{@const files = shot.files as ShotFiles}
											{@const approved = files?.image_generation?.approved ?? []}
											{@const sel = isSelected('frames', shot.id)}
											{@const first = approved[0]}
											<button
												onclick={() => selectSlot('frames', shot)}
												title="{shot.id} — {approved.length} frame(s)"
												style="position:absolute;top:2px;bottom:2px;{slotStyle(shot.start_s, shot.end_s, timelineData.total_duration_s)}"
												class="flex gap-0.5 items-stretch px-0.5 rounded overflow-hidden border transition-all
												       {sel ? 'ring-2 ring-fuchsia-400 border-fuchsia-300 bg-fuchsia-50' : 'border-fuchsia-200 bg-white hover:border-fuchsia-300'}"
											>
												{#if first?.first_frame}
													<img
														src="{API_BASE}/api/files/serve?path={encodeURIComponent(first.first_frame)}"
														alt="first"
														class="h-full w-auto object-cover rounded-sm"
													/>
												{/if}
												{#if first?.last_frame}
													<img
														src="{API_BASE}/api/files/serve?path={encodeURIComponent(first.last_frame)}"
														alt="last"
														class="h-full w-auto object-cover rounded-sm"
													/>
												{/if}
												{#if !first?.first_frame && !first?.last_frame}
													<span class="text-[9px] text-fuchsia-400 self-center px-1">{shot.id}</span>
												{/if}
											</button>
										{/each}
									</div>
								</div>
							{/if}
						{/if}

						<!-- Assets row -->
						{#if timelineData.assets && Object.keys(timelineData.assets).length > 0}
							{@const char = timelineData.assets.character}
							{@const prod = timelineData.assets.product}
							<div class="flex border-t-2 border-slate-200 bg-slate-50/40">
								<div class="w-24 shrink-0 border-r border-slate-100 flex items-center justify-end pr-3">
									<span class="text-[9px] font-semibold uppercase tracking-wide text-slate-400">Assets</span>
								</div>
								<div class="flex-1 flex items-center gap-2 px-3 py-2 flex-wrap">
									{#if char?.available && char.approved_image}
										<button
											onclick={() => selectAsset(char.approved_image!)}
											title={char.generation_prompt ?? 'Character'}
											class="flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs transition-colors
											       {selectedAssetPath === char.approved_image
												       ? 'bg-slate-800 text-white border-slate-800'
												       : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'}"
										>
											<span>👤</span>
											<span class="font-medium">Character</span>
											{#if char.higgsfield_job_id}
												<span class="font-mono text-[9px] opacity-50 max-w-[80px] truncate">{char.higgsfield_job_id}</span>
											{/if}
										</button>
									{/if}
									{#if prod?.available}
										{#each prod.files as f, i}
											<button
												onclick={() => selectAsset(f)}
												title={f}
												class="flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs transition-colors
												       {selectedAssetPath === f
													       ? 'bg-slate-800 text-white border-slate-800'
													       : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'}"
											>
												<span>📦</span>
												<span class="font-medium">Product {prod.files.length > 1 ? i + 1 : ''}</span>
											</button>
										{/each}
									{/if}
								</div>
							</div>
						{/if}

					</div>

				{:else}
					<div class="flex items-center justify-center h-40">
						<p class="text-sm text-slate-400 italic">Select campaign → angle → arc → hook, then press Load timeline.</p>
					</div>
				{/if}

				<!-- Ad Images row: non-time-based, loads when arc is selected -->
				{#if imgAdsData && imgAdsData.concepts.some((c) => c.image)}
					<div class="flex border-t-2 border-slate-200 bg-indigo-50/20">
						<div class="w-24 shrink-0 border-r border-slate-100 flex items-center justify-end pr-3">
							<span class="text-[9px] font-semibold uppercase tracking-wide text-slate-400">Ad Images</span>
						</div>
						<div class="flex-1 flex items-center gap-2 px-3 py-2 flex-wrap">
							{#each imgAdsData.concepts as concept}
								{#if concept.image}
									<button
										onclick={() => selectAsset(concept.image!)}
										title="{concept.concept}{concept.headline_ptbr ? ' — ' + concept.headline_ptbr : ''}"
										class="relative shrink-0 rounded overflow-hidden border-2 transition-all
										       {selectedAssetPath === concept.image
											       ? 'border-slate-700 ring-2 ring-slate-400/50'
											       : 'border-slate-200 hover:border-indigo-400'}"
									>
										<img
											src="{API_BASE}/api/files/serve?path={encodeURIComponent(concept.image)}"
											alt={concept.concept}
											class="w-[120px] h-[120px] object-cover block"
										/>
										{#if concept.status !== 'generated'}
											<div class="absolute bottom-0 inset-x-0 bg-black/60 text-white text-[8px] text-center leading-tight py-0.5">{concept.status}</div>
										{/if}
									</button>
								{/if}
							{/each}
						</div>
					</div>
				{/if}

			</div>

			<!-- ── Drag handle ───────────────────────────────────────────────── -->
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div
				onmousedown={(e) => {
					detailDragging = true;
					detailDragStartY = e.clientY;
					detailDragStartH = detailHeight;
					e.preventDefault();
				}}
				ontouchstart={(e) => {
					detailDragging = true;
					detailDragStartY = e.touches[0].clientY;
					detailDragStartH = detailHeight;
				}}
				class="shrink-0 h-2 cursor-row-resize flex items-center justify-center border-y border-slate-200
				       {detailDragging ? 'bg-emerald-100' : 'bg-slate-100 hover:bg-slate-200'} transition-colors"
			>
				<div class="w-10 h-0.5 rounded-full bg-slate-300"></div>
			</div>

			<!-- ── Detail panel (bottom) ─────────────────────────────────────── -->
			<div
				class="shrink-0 bg-white overflow-hidden flex"
				style="height:{detailHeight}px"
			>

				{#if !selectedSlot && !selectedAssetPath}
					<div class="flex-1 flex items-center justify-center">
						<p class="text-xs text-slate-400 italic">Click a slot or an asset above to inspect it.</p>
					</div>

				{:else if selectedAssetPath}
					{#if isAdImage}
						{@const concept = adImageConcepts[selectedConceptIdx]}
						<!-- Left: concept metadata -->
						<div class="w-48 shrink-0 border-r border-slate-100 px-4 py-3 flex flex-col gap-1.5 justify-center">
							<p class="text-[10px] font-semibold uppercase tracking-wide text-slate-400">Ad Image</p>
							<p class="text-xs font-semibold text-slate-700 leading-snug">{concept.concept}</p>
							{#if concept.headline_ptbr}
								<p class="text-[11px] text-slate-500 italic leading-tight">{concept.headline_ptbr}</p>
							{/if}
							<p class="text-[10px] text-slate-400 mt-auto">{selectedConceptIdx + 1} / {adImageConcepts.length}</p>
						</div>
						<!-- Right: prev arrow + image + next arrow (centered, hugs image) -->
						<div class="flex-1 flex items-center overflow-hidden py-2 pl-3">
							<div class="flex items-center gap-2">
								<button
									onclick={prevConcept}
									class="shrink-0 w-7 h-7 flex items-center justify-center rounded-full
									       bg-slate-800 text-white hover:bg-slate-600
									       transition-colors text-xl leading-none"
								>‹</button>
								<div class="overflow-y-auto max-h-full px-1">
									<FileViewer filePath={selectedAssetPath} />
								</div>
								<button
									onclick={nextConcept}
									class="shrink-0 w-7 h-7 flex items-center justify-center rounded-full
									       bg-slate-800 text-white hover:bg-slate-600
									       transition-colors text-xl leading-none"
								>›</button>
							</div>
						</div>
					{:else}
						<!-- Regular asset viewer -->
						<div class="w-48 shrink-0 border-r border-slate-100 px-4 py-3 flex flex-col justify-center gap-1">
							<p class="text-[10px] font-semibold uppercase tracking-wide text-slate-400">Asset</p>
							<p class="text-xs font-mono text-slate-600 break-all">{selectedAssetPath.split('/').pop()}</p>
						</div>
						<div class="flex-1 px-4 py-3 overflow-y-auto">
							<FileViewer filePath={selectedAssetPath} />
						</div>
					{/if}

				{:else if selectedSlot && selectedSlot.trackKey === 'frames'}
					<!-- Frames detail: first/last frame images + metadata -->
					{@const imgGen = (selectedSlot.item.files as ShotFiles | undefined)?.image_generation}
					<div class="w-64 shrink-0 border-r border-slate-100 px-4 py-3 overflow-y-auto space-y-2">
						<div class="flex items-center gap-2 flex-wrap">
							<span class="font-mono text-sm font-bold text-slate-900">{selectedSlot.item.id}</span>
							<span class="text-[10px] px-1.5 py-0.5 rounded-full font-medium bg-fuchsia-100 text-fuchsia-700">frames</span>
						</div>
						<p class="text-xs text-slate-700 leading-relaxed">{selectedSlot.item.label}</p>
						<div class="flex gap-1.5 text-[11px]">
							<span class="text-slate-400 font-medium shrink-0">time:</span>
							<span class="font-mono text-slate-600">{selectedSlot.item.start_s}s – {selectedSlot.item.end_s}s</span>
						</div>
						{#if imgGen}
							<p class="text-[10px] text-slate-400">{imgGen.attempts_count} attempt(s) · {imgGen.approved.length} approved</p>
							{#each imgGen.approved as frame}
								<div class="pt-1 border-t border-slate-100 space-y-0.5">
									<p class="text-[10px] font-semibold text-slate-500">Attempt {frame.attempt}</p>
									<div class="flex gap-1 text-[10px]"><span class="text-slate-300">model:</span><span class="font-mono">{frame.model}</span></div>
									{#if frame.first_frame_job_id}
										<div class="flex gap-1 text-[10px]"><span class="text-slate-300">first job:</span><span class="font-mono truncate text-[9px]">{frame.first_frame_job_id}</span></div>
									{/if}
									{#if frame.last_frame_job_id}
										<div class="flex gap-1 text-[10px]"><span class="text-slate-300">last job:</span><span class="font-mono truncate text-[9px]">{frame.last_frame_job_id}</span></div>
									{/if}
								</div>
							{/each}
						{/if}
					</div>
					<div class="flex-1 overflow-y-auto px-4 py-3">
						{#if !imgGen || imgGen.approved.length === 0}
							<p class="text-xs text-slate-400 italic">No approved frames.</p>
						{:else}
							<div class="space-y-6">
								{#each imgGen.approved as frame}
									<div class="space-y-2">
										<p class="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">Attempt {frame.attempt} — {frame.model}</p>
										<div class="flex gap-3 flex-wrap">
											{#if frame.first_frame}
												<div class="space-y-1">
													<p class="text-[9px] text-slate-300 uppercase tracking-wide">First frame</p>
													<img
														src="{API_BASE}/api/files/serve?path={encodeURIComponent(frame.first_frame)}"
														alt="first frame {frame.attempt}"
														class="max-h-40 max-w-full rounded-lg border border-slate-200 object-contain"
													/>
												</div>
											{/if}
											{#if frame.last_frame}
												<div class="space-y-1">
													<p class="text-[9px] text-slate-300 uppercase tracking-wide">Last frame</p>
													<img
														src="{API_BASE}/api/files/serve?path={encodeURIComponent(frame.last_frame)}"
														alt="last frame {frame.attempt}"
														class="max-h-40 max-w-full rounded-lg border border-slate-200 object-contain"
													/>
												</div>
											{/if}
										</div>
									</div>
								{/each}
							</div>
						{/if}
					</div>

				{:else if selectedSlot}
					<!-- Slot metadata -->
					<div class="w-64 shrink-0 border-r border-slate-100 px-4 py-3 overflow-y-auto space-y-2">
						<div class="flex items-center gap-2 flex-wrap">
							<span class="font-mono text-sm font-bold text-slate-900">{selectedSlot.item.id}</span>
							{#if selectedSlot.trackKey === 'shots'}
								{@const gs = selectedSlot.item.gen_status as string | undefined}
								{#if gs}
									<span class="text-[10px] px-1.5 py-0.5 rounded-full font-medium {GEN_STATUS[gs] ?? 'bg-slate-100 text-slate-600'}">{gs}</span>
								{/if}
							{/if}
						</div>
						<p class="text-xs text-slate-700 leading-relaxed">{selectedSlot.item.label}</p>
						{#each extraFields(selectedSlot.item) as { k, v }}
							<div class="flex gap-1.5 text-[11px]">
								<span class="text-slate-400 font-medium shrink-0">{k}:</span>
								<span class="text-slate-600">{v}</span>
							</div>
						{/each}
						<div class="flex gap-1.5 text-[11px]">
							<span class="text-slate-400 font-medium shrink-0">time:</span>
							<span class="font-mono text-slate-600">{selectedSlot.item.start_s}s – {selectedSlot.item.end_s}s</span>
						</div>
						<!-- Shot image generation info -->
						{#if selectedSlot.trackKey === 'shots'}
							{@const imgGen = (selectedSlot.item.files as ShotFiles | undefined)?.image_generation}
							{#if imgGen && imgGen.approved.length > 0}
								<div class="pt-1 border-t border-slate-100 space-y-1">
									<p class="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">Generations ({imgGen.attempts_count})</p>
									{#each imgGen.approved as frame}
										<div class="text-[10px] text-slate-500 space-y-0.5">
											<div class="flex gap-1"><span class="text-slate-300">model:</span><span class="font-mono">{frame.model}</span></div>
											{#if frame.first_frame_job_id}
												<div class="flex gap-1"><span class="text-slate-300">first:</span><span class="font-mono truncate">{frame.first_frame_job_id}</span></div>
											{/if}
											{#if frame.last_frame_job_id}
												<div class="flex gap-1"><span class="text-slate-300">last:</span><span class="font-mono truncate">{frame.last_frame_job_id}</span></div>
											{/if}
										</div>
									{/each}
								</div>
							{/if}
						{/if}
					</div>
					<!-- Viewer: video if generated, else prompt to use asset bar -->
					<div class="flex-1 px-4 py-3 overflow-y-auto">
						{#if viewerPath}
							<FileViewer filePath={viewerPath} />
						{:else if selectedSlot.trackKey === 'shots'}
							<div class="flex flex-col items-center justify-center h-full gap-1 text-center">
								<p class="text-xs text-slate-400 italic">No video generated yet.</p>
								{#if timelineData?.assets?.character?.approved_image}
									<p class="text-[10px] text-slate-300">Click Character in the Assets bar to see the reference.</p>
								{/if}
							</div>
						{:else}
							<div class="flex items-center justify-center h-full">
								<p class="text-xs text-slate-400 italic">Text track — no media asset.</p>
							</div>
						{/if}
					</div>
				{/if}

			</div>

		</div>
	</div>
</div>
