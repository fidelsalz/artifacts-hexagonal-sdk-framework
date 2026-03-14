<script lang="ts">
  import { onMount } from 'svelte';
  import { API_BASE_URL } from '$lib/config.js';
  import FileEditorModal from './FileEditorModal.svelte';

  type Entry    = { name: string; type: 'dir' | 'file'; path: string };
  type Shortcut = { label: string; path: string };
  type FileData = { path: string; content: string };

  let {
    shortcuts    = [],
    changedPaths = new Set<string>(),
    initialPath  = '',
  }: {
    shortcuts:    Shortcut[];
    changedPaths?: Set<string>;
    initialPath?:  string;
  } = $props();

  onMount(() => {
    if (initialPath) loadDir(initialPath);
  });

  let currentPath = $state('');
  let entries     = $state<Entry[]>([]);
  let loading     = $state(false);
  let error       = $state('');
  let editorFile  = $state<FileData | null>(null);

  const breadcrumbs = $derived(() => {
    if (!currentPath) return [];
    const parts = currentPath.split('/').filter(Boolean);
    return parts.map((part, i) => ({
      label: part,
      path: '/' + parts.slice(0, i + 1).join('/'),
    }));
  });

  async function loadDir(path: string) {
    loading = true;
    error = '';
    try {
      const r = await fetch(`${API_BASE_URL}/api/files/list?path=${encodeURIComponent(path)}`);
      if (!r.ok) { const j = await r.json(); throw new Error(j.detail ?? r.statusText); }
      const data = await r.json();
      currentPath = data.path;
      entries = data.entries;
    } catch (e: any) {
      error = e.message ?? 'Failed to load directory';
    } finally {
      loading = false;
    }
  }

  async function openFile(path: string) {
    loading = true;
    error = '';
    try {
      const r = await fetch(`${API_BASE_URL}/api/files/read?path=${encodeURIComponent(path)}`);
      if (!r.ok) { const j = await r.json(); throw new Error(j.detail ?? r.statusText); }
      const data = await r.json();
      editorFile = { path: data.path, content: data.content };
    } catch (e: any) {
      error = e.message ?? 'Failed to read file';
    } finally {
      loading = false;
    }
  }
</script>

<div class="flex flex-col gap-2 rounded-md border bg-muted/30 p-3 text-xs font-mono">

  <!-- Quick-nav shortcuts -->
  {#if shortcuts.length > 0}
    <div class="flex flex-wrap gap-1">
      {#each shortcuts as sc}
        <button
          onclick={() => loadDir(sc.path)}
          class="px-2 py-0.5 rounded border text-[11px] font-sans font-medium bg-background hover:bg-muted transition-colors"
        >[{sc.label}]</button>
      {/each}
    </div>
  {/if}

  <!-- Breadcrumb -->
  {#if currentPath}
    <div class="flex flex-wrap items-center gap-0.5 text-muted-foreground text-[11px]">
      {#each breadcrumbs() as crumb, i}
        <button
          onclick={() => loadDir(crumb.path)}
          class="hover:text-foreground hover:underline transition-colors"
        >{crumb.label}</button>
        {#if i < breadcrumbs().length - 1}<span class="opacity-40">/</span>{/if}
      {/each}
      <span class="opacity-30 ml-0.5">/</span>
    </div>
  {/if}

  <!-- Entries list -->
  {#if loading}
    <p class="text-muted-foreground italic text-[11px] px-1">Loading...</p>
  {:else if currentPath}
    <div class="flex flex-col border rounded bg-background divide-y">
      {#each entries as entry}
        <button
          onclick={() => entry.type === 'dir' ? loadDir(entry.path) : openFile(entry.path)}
          class="flex items-center gap-1.5 px-2 py-1 text-left hover:bg-muted/50 transition-colors text-[11px]"
        >
          <span>{entry.type === 'dir' ? '📁' : '📄'}</span>
          <span class="flex-1 truncate">{entry.name}{entry.type === 'dir' ? '/' : ''}</span>
          {#if changedPaths.has(entry.path)}
            <span class="text-amber-500 font-bold" title="Changed">●</span>
          {/if}
        </button>
      {/each}
      {#if entries.length === 0}
        <p class="px-2 py-1 text-muted-foreground italic text-[11px]">(empty)</p>
      {/if}
    </div>
  {:else}
    <p class="text-muted-foreground italic text-[11px] px-1">Use a shortcut or navigate to a directory.</p>
  {/if}

  <!-- Error -->
  {#if error}
    <p class="text-red-500 text-[11px] px-1">{error}</p>
  {/if}

</div>

<!-- File editor modal (portal, rendered outside the explorer div) -->
<FileEditorModal
  file={editorFile}
  onclose={() => (editorFile = null)}
/>
