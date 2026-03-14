<script lang="ts">
  import { Separator } from '$lib/components/ui/separator';
  import { Button } from '$lib/components/ui/button';
  import AgentStatusCard from '$lib/components/AgentStatusCard.svelte';
  import FileEditorModal from '$lib/components/FileEditorModal.svelte';
  import { caseState } from '$lib/stores/caseStore.svelte.js';
  import { API_BASE_URL } from '$lib/config.js';

  type FileData = { path: string; content: string };
  let editorFile = $state<FileData | null>(null);

  async function openConfig() {
    const r = await fetch(`${API_BASE_URL}/api/agents/config-file`);
    if (r.ok) editorFile = await r.json();
  }

  const rows = [
    { id: 'ports',              label: 'Ports Agent',        type: 'coding'    as const },
    { id: 'ports-validator',    label: 'Ports Validator',    type: 'validator' as const },
    { id: 'adapters',           label: 'Adapters Agent',     type: 'coding'    as const },
    { id: 'adapters-validator', label: 'Adapters Validator', type: 'validator' as const },
    { id: 'hexagon',            label: 'Hexagon Agent',      type: 'coding'    as const },
    { id: 'hexagon-validator',  label: 'Hexagon Validator',  type: 'validator' as const },
    { id: 'infra',              label: 'Infra Agent',        type: 'coding'    as const },
    { id: 'infra-validator',    label: 'Infra Validator',    type: 'validator' as const },
    { id: 'contracts-writer',   label: 'Contracts Writer',   type: 'workspace' as const },
  ] as const;

  const agentRows = $derived(
    rows.map((row) => {
      const storeAgent = caseState.agents.find((a) => a.id === row.id);
      return {
        ...row,
        status: storeAgent?.status ?? 'idle',
        mode: (storeAgent as any)?.mode,
        lastRunAt: (storeAgent as any)?.lastRunAt ?? null,
      };
    })
  );

  const dividerAfter = new Set([1, 3, 5, 7]);
</script>

<div class="py-6 px-2">
  <!-- Sub-header bar -->
  <div class="flex items-center justify-between mb-6">
    <div class="flex items-center gap-2">
      <Button variant="default">Run All Coding Agents</Button>
      <Button variant="outline" onclick={openConfig}>Edit Config</Button>
    </div>
    <div class="flex items-center gap-4 text-sm text-muted-foreground">
      <span>Cost: <span class="font-medium text-foreground">${caseState.totalCostUsd.toFixed(2)}</span></span>
      <span>Case: <span class="font-medium text-foreground">{caseState.caseId}</span></span>
    </div>
  </div>

  <!-- Agent table -->
  <div class="rounded-lg border bg-card overflow-hidden">
    <div class="grid grid-cols-[1fr_auto] gap-4 px-4 py-2 bg-muted/50 border-b text-xs font-semibold uppercase tracking-wide text-muted-foreground">
      <span>Agent</span>
      <span>Actions</span>
    </div>

    {#each agentRows as row, i}
      <div class="px-3 py-2">
        <AgentStatusCard agent={row} />
      </div>
      {#if dividerAfter.has(i)}
        <Separator />
      {/if}
    {/each}
  </div>
</div>

<FileEditorModal file={editorFile} onclose={() => (editorFile = null)} />
