<script lang="ts">
	import { API_BASE } from '$lib/config';
	import { marked } from 'marked';

	let { filePath }: { filePath: string | null } = $props();

	let content = $state<string | null>(null);
	let editContent = $state('');
	let editing = $state(false);
	let showSource = $state(false);
	let loading = $state(false);
	let saving = $state(false);
	let error = $state('');

	const IMAGE_EXTS = new Set(['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'avif']);
	const VIDEO_EXTS = new Set(['mp4', 'webm', 'mov', 'mkv']);
	const AUDIO_EXTS = new Set(['mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac']);

	type FileKind = 'image' | 'video' | 'audio' | 'markdown' | 'text';

	const fileKind = $derived((): FileKind => {
		const e = filePath?.split('.').pop()?.toLowerCase() ?? '';
		if (IMAGE_EXTS.has(e)) return 'image';
		if (VIDEO_EXTS.has(e)) return 'video';
		if (AUDIO_EXTS.has(e)) return 'audio';
		if (e === 'md') return 'markdown';
		return 'text';
	});

	const isMedia = $derived(['image', 'video', 'audio'].includes(fileKind()));

	const serveUrl = $derived(
		filePath ? `${API_BASE}/api/files/serve?path=${encodeURIComponent(filePath)}` : ''
	);

	$effect(() => {
		const path = filePath;
		if (!path) {
			content = null;
			editing = false;
			showSource = false;
			error = '';
			return;
		}
		// Binary media — served directly via serveUrl, no text fetch needed
		if (isMedia) {
			content = null;
			loading = false;
			editing = false;
			error = '';
			return;
		}
		loading = true;
		editing = false;
		showSource = false;
		error = '';
		fetch(`${API_BASE}/api/files/read?path=${encodeURIComponent(path)}`)
			.then((r) => {
				if (!r.ok) throw new Error(`HTTP ${r.status}`);
				return r.json();
			})
			.then((data) => {
				content = data.content;
				editContent = data.content;
			})
			.catch((e) => {
				error = e instanceof Error ? e.message : String(e);
			})
			.finally(() => {
				loading = false;
			});
	});

	function startEdit() {
		editContent = content ?? '';
		editing = true;
	}

	function cancelEdit() {
		editing = false;
	}

	async function save() {
		if (!filePath) return;
		saving = true;
		error = '';
		try {
			const res = await fetch(`${API_BASE}/api/files/write`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ path: filePath, content: editContent }),
			});
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			content = editContent;
			editing = false;
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			saving = false;
		}
	}

	function onKeydown(e: KeyboardEvent) {
		if ((e.ctrlKey || e.metaKey) && e.key === 's') {
			e.preventDefault();
			save();
		}
		if (e.key === 'Escape') cancelEdit();
	}

	const renderedHtml = $derived(
		fileKind() === 'markdown' && content ? String(marked.parse(content)) : ''
	);

</script>

{#if !filePath}
	<div class="flex items-center gap-2 text-xs text-slate-400 italic px-1 py-2 min-h-[40px]">
		<span>📄</span> Select a file from the tree to view it.
	</div>
{:else if loading}
	<div class="text-xs text-slate-400 animate-pulse px-1 py-2">Loading…</div>
{:else if error}
	<div class="text-xs text-red-600 px-1 py-2">{error}</div>
{:else}
	<!-- Header bar -->
	<div class="flex items-center gap-2 mb-2">
		<span class="text-xs font-mono text-slate-500 truncate flex-1">{filePath.split('/').pop()}</span>
		{#if isMedia}
			<a
				href="{serveUrl}&download=true"
				class="text-[11px] px-2 py-0.5 rounded border border-slate-200 text-slate-600 hover:bg-slate-100 transition-colors"
			>
				Download
			</a>
		{:else}
			{#if !editing}
				{#if fileKind() === 'markdown'}
					<button
						onclick={() => (showSource = !showSource)}
						class="text-[11px] px-2 py-0.5 rounded border border-slate-200 text-slate-500 hover:bg-slate-100 transition-colors"
					>
						{showSource ? 'Preview' : 'Source'}
					</button>
				{/if}
				<button
					onclick={startEdit}
					class="text-[11px] px-2 py-0.5 rounded border border-slate-200 text-slate-600 hover:bg-slate-100 transition-colors"
				>
					Edit
				</button>
			{:else}
				<span class="text-[10px] text-slate-400">Ctrl+S to save · Esc to cancel</span>
				<button
					onclick={cancelEdit}
					class="text-[11px] px-2 py-0.5 rounded border border-slate-200 text-slate-600 hover:bg-slate-100 transition-colors"
				>
					Cancel
				</button>
				<button
					onclick={save}
					disabled={saving}
					class="text-[11px] px-2 py-0.5 rounded border font-medium transition-colors
					       {saving ? 'border-slate-200 text-slate-400' : 'border-emerald-500 bg-emerald-600 text-white hover:bg-emerald-500'}"
				>
					{saving ? 'Saving…' : 'Save'}
				</button>
			{/if}
		{/if}
	</div>

	{#if fileKind() === 'image'}
		<a href={serveUrl} target="_blank" rel="noopener noreferrer">
			<img
				src={serveUrl}
				alt={filePath.split('/').pop()}
				class="max-w-full max-h-[360px] object-contain rounded-lg border border-slate-200"
			/>
		</a>
	{:else if fileKind() === 'video'}
		<video controls class="w-full rounded-lg border border-slate-200 max-h-[480px]">
			<source src={serveUrl} />
		</video>
	{:else if fileKind() === 'audio'}
		<audio controls class="w-full mt-2">
			<source src={serveUrl} />
		</audio>
	{:else if !editing}
		{#if fileKind() === 'markdown' && !showSource}
			<div
				class="markdown-body text-sm bg-white border border-slate-200 rounded-lg p-4
				       max-h-[480px] overflow-y-auto"
			>
				<!-- eslint-disable-next-line svelte/no-at-html-tags -->
				{@html renderedHtml}
			</div>
		{:else}
			<pre class="text-xs font-mono text-slate-800 whitespace-pre-wrap break-words leading-relaxed
			            bg-slate-50 border border-slate-200 rounded-lg p-4 overflow-x-auto
			            max-h-[480px] overflow-y-auto">{content}</pre>
		{/if}
	{:else}
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<textarea
			bind:value={editContent}
			onkeydown={onKeydown}
			spellcheck={false}
			class="w-full text-xs font-mono text-slate-800 bg-slate-50 border border-emerald-400
			       rounded-lg p-4 resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500/40
			       leading-relaxed min-h-[240px] max-h-[480px]"
			rows={Math.max(10, (editContent.match(/\n/g)?.length ?? 0) + 3)}
		></textarea>
	{/if}

	{#if error}
		<p class="mt-1 text-xs text-red-600">{error}</p>
	{/if}
{/if}

<style>
	.markdown-body :global(h1) { font-size: 1.15rem; font-weight: 700; margin: 0.75rem 0 0.4rem; color: #0f172a; }
	.markdown-body :global(h2) { font-size: 1rem; font-weight: 600; margin: 0.6rem 0 0.3rem; color: #1e293b; }
	.markdown-body :global(h3) { font-size: 0.9rem; font-weight: 600; margin: 0.5rem 0 0.25rem; color: #334155; }
	.markdown-body :global(p)  { margin: 0.35rem 0; line-height: 1.6; color: #334155; }
	.markdown-body :global(ul),
	.markdown-body :global(ol) { padding-left: 1.25rem; margin: 0.3rem 0; color: #334155; }
	.markdown-body :global(li) { margin: 0.15rem 0; line-height: 1.5; }
	.markdown-body :global(code) { background: #f1f5f9; border-radius: 3px; padding: 0.1em 0.35em; font-size: 0.8em; font-family: monospace; color: #0f172a; }
	.markdown-body :global(pre) { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.75rem; overflow-x: auto; margin: 0.5rem 0; }
	.markdown-body :global(pre code) { background: none; padding: 0; }
	.markdown-body :global(blockquote) { border-left: 3px solid #e2e8f0; padding-left: 0.75rem; color: #64748b; margin: 0.5rem 0; }
	.markdown-body :global(a) { color: #059669; text-decoration: underline; }
	.markdown-body :global(hr) { border: none; border-top: 1px solid #e2e8f0; margin: 0.75rem 0; }
	.markdown-body :global(table) { width: 100%; border-collapse: collapse; font-size: 0.8rem; margin: 0.5rem 0; }
	.markdown-body :global(th) { background: #f8fafc; border: 1px solid #e2e8f0; padding: 0.35rem 0.6rem; font-weight: 600; text-align: left; color: #1e293b; }
	.markdown-body :global(td) { border: 1px solid #e2e8f0; padding: 0.3rem 0.6rem; color: #334155; }
</style>
