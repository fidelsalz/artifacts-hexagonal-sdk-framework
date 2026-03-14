<script lang="ts">
  import * as Card from '$lib/components/ui/card';
  import { Badge } from '$lib/components/ui/badge';
  import { Button } from '$lib/components/ui/button';
  import { runAgent, toggleValidatorMode } from '$lib/stores/caseStore.svelte.js';

  type AgentRow =
    | { id: string; label: string; type: 'coding'; status: string; lastRunAt?: string | null }
    | { id: string; label: string; type: 'validator'; status: string; mode: 'auto' | 'manual'; lastRunAt?: string | null }
    | { id: string; label: string; type: 'workspace'; status: string; lastRunAt?: string | null };

  let { agent }: { agent: AgentRow } = $props();

  function fmtTime(iso: string): string {
    return new Date(iso).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  const statusColor: Record<string, string> = {
    idle:    'secondary',
    running: 'default',
    done:    'outline',
    error:   'destructive',
  };
</script>

<Card.Root class="w-full">
  <Card.Content class="flex items-center justify-between py-3 px-4">
    <!-- Name + status -->
    <div class="flex items-center gap-3 min-w-0">
      <span class="text-sm font-medium truncate">{agent.label}</span>
      {#if agent.lastRunAt}
        <span class="text-[9px] text-muted-foreground/50 tabular-nums">{fmtTime(agent.lastRunAt)}</span>
      {/if}
      <Badge variant={statusColor[agent.status] as any ?? 'secondary'}>
        {agent.status}
      </Badge>
      {#if agent.type === 'validator'}
        <Badge variant="outline" class="text-xs uppercase tracking-wide">
          {agent.mode}
        </Badge>
      {/if}
    </div>

    <!-- Actions -->
    <div class="flex items-center gap-2 shrink-0 ml-4">
      {#if agent.type === 'coding'}
        <Button size="sm" variant="outline" onclick={() => runAgent(agent.id)} disabled={agent.status === 'running'}>Start</Button>
        <Button size="sm" variant="ghost" href="/agents">Output</Button>
      {:else if agent.type === 'validator'}
        {#if agent.mode === 'auto'}
          <Button size="sm" variant="outline" onclick={() => toggleValidatorMode(agent.id)}>Disable Auto</Button>
        {:else}
          <Button size="sm" variant="ghost" onclick={() => toggleValidatorMode(agent.id)}>Enable Auto</Button>
          <Button size="sm" variant="default" onclick={() => runAgent(agent.id)} disabled={agent.status === 'running'}>Run Validator</Button>
        {/if}
      {:else if agent.type === 'workspace'}
        <Button size="sm" variant="default" href="/agents">Open Workspace</Button>
      {/if}
    </div>
  </Card.Content>
</Card.Root>
