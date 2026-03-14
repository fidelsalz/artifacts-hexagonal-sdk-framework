<script lang="ts">
  import AgentTabPanel from '$lib/components/AgentTabPanel.svelte';
  import CodingAgentPanel from '$lib/components/CodingAgentPanel.svelte';
  import ConversationPanel from '$lib/components/ConversationPanel.svelte';
  import DashboardPanel from '$lib/components/DashboardPanel.svelte';
  import { caseState } from '$lib/stores/caseStore.svelte.js';

  type SoloTab = { id: string; label: string; kind: 'solo'; agentId: string };
  type PairTab  = { id: string; label: string; kind: 'pair'; agentId: string; validatorId: string };
  type DashTab  = { id: 'dashboard'; label: string; kind: 'dashboard' };
  type Tab = DashTab | SoloTab | PairTab;

  const tabs: Tab[] = [
    { id: 'dashboard',       label: 'Dashboard',  kind: 'dashboard' },
    { id: 'human-assistant', label: 'human-asst', kind: 'solo', agentId: 'human-assistant' },
    { id: 'contracts',       label: 'contracts',  kind: 'solo', agentId: 'contracts-writer' },
    { id: 'ports',           label: 'ports',      kind: 'pair', agentId: 'ports',    validatorId: 'ports-validator' },
    { id: 'adapters',        label: 'adapters',   kind: 'pair', agentId: 'adapters', validatorId: 'adapters-validator' },
    { id: 'hexagon',         label: 'hexagon',    kind: 'pair', agentId: 'hexagon',  validatorId: 'hexagon-validator' },
    { id: 'infra',           label: 'infra',      kind: 'pair', agentId: 'infra',    validatorId: 'infra-validator' },
  ];

  let activeTab = $state('dashboard');

  const activeTab$ = $derived(tabs.find((t) => t.id === activeTab)!);

  function resolveAgent(id: string) {
    const stored = caseState.agents.find((a) => a.id === id);
    return {
      id,
      label:        stored?.label        ?? id,
      commType:     (stored?.commType    ?? 'sse') as 'ws' | 'sse',
      status:       (stored?.status      ?? 'idle') as 'idle' | 'running' | 'done' | 'error',
      messages:     stored?.messages     ?? [],
      changedPaths: (stored as any)?.changedPaths ?? new Set<string>(),
    };
  }
</script>

<div class="max-w-[1075px] mx-auto py-6 px-4">
  <!-- Tab bar -->
  <div class="flex gap-1 border-b mb-6 overflow-x-auto">
    {#each tabs as tab}
      <button
        onclick={() => (activeTab = tab.id)}
        class="px-3 py-2 text-sm font-medium whitespace-nowrap rounded-t-md border-b-2 transition-colors
               {activeTab === tab.id
                 ? 'border-primary text-primary bg-muted/30'
                 : 'border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/20'}"
      >
        {tab.label}
      </button>
    {/each}
  </div>

  <!-- Non-WS active content -->
  {#if activeTab$.kind === 'dashboard'}
    <DashboardPanel />

  {:else if activeTab$.kind === 'pair'}
    <CodingAgentPanel
      agent={resolveAgent(activeTab$.agentId)}
      validator={resolveAgent(activeTab$.validatorId)}
    />

  {:else if activeTab$.kind === 'solo'}
    {@const ag = resolveAgent(activeTab$.agentId)}
    {#if ag.commType !== 'ws'}
      <AgentTabPanel agent={ag} />
    {/if}
  {/if}

  <!-- WS conversation panels: always mounted so each keeps its own session.
       Shown/hidden with CSS — switching tabs never destroys the connection. -->
  {#each tabs as tab}
    {#if tab.kind === 'solo'}
      {@const ag = resolveAgent(tab.agentId)}
      {#if ag.commType === 'ws'}
        <div class={activeTab === tab.id ? '' : 'hidden'}>
          <ConversationPanel agent={ag} />
        </div>
      {/if}
    {/if}
  {/each}
</div>
