<script lang="ts">
  import { Badge } from '$lib/components/ui/badge';
  import { Button } from '$lib/components/ui/button';
  import { Separator } from '$lib/components/ui/separator';

  type AgentMessage = { type: 'assistant' | 'user' | 'status' | 'result'; text?: string };
  type AgentConfig = {
    id: string;
    label: string;
    commType: 'ws' | 'sse';
    status: 'idle' | 'running' | 'done' | 'error';
    messages: AgentMessage[];
  };

  let { agent }: { agent: AgentConfig } = $props();

  let inputText = $state('');

  const statusColor: Record<string, string> = {
    idle:    'bg-gray-100 text-gray-600',
    running: 'bg-blue-100 text-blue-700 animate-pulse',
    done:    'bg-green-100 text-green-700',
    error:   'bg-red-100 text-red-700',
  };

  const commBadgeColor: Record<string, string> = {
    ws:  'bg-violet-100 text-violet-700 border-violet-200',
    sse: 'bg-sky-100 text-sky-700 border-sky-200',
  };
</script>

<div class="flex flex-col gap-3 rounded-lg border bg-card p-4">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-2">
      <span class="font-semibold text-sm">{agent.label}</span>
      <span class="text-xs font-medium px-2 py-0.5 rounded-full border {commBadgeColor[agent.commType]}">
        {agent.commType.toUpperCase()}
      </span>
    </div>
    <span class="text-xs font-medium px-2 py-0.5 rounded-full {statusColor[agent.status]}">
      {agent.status === 'running' ? '● ACTIVE' : agent.status.toUpperCase()}
    </span>
  </div>

  <Separator />

  <!-- Run / Stop buttons -->
  <div class="flex gap-2">
    <Button
      size="sm"
      variant="default"
      disabled={agent.status === 'running'}
    >
      Run
    </Button>
    <Button
      size="sm"
      variant="outline"
      disabled={agent.status !== 'running'}
    >
      Stop
    </Button>
  </div>

  <!-- Output stream -->
  <div class="h-48 overflow-y-auto rounded border bg-muted/40 p-2 text-xs font-mono divide-y divide-border">
    {#if agent.messages.length === 0 && agent.status === 'idle'}
      <p class="p-2 text-muted-foreground italic">No output yet.</p>
    {/if}
    {#each agent.messages as msg}
      {#if msg.type === 'status'}
        <div class="px-2 py-1 text-muted-foreground italic">[status] {msg.text}</div>
      {:else if msg.type === 'assistant'}
        <div class="px-2 py-1.5 text-foreground whitespace-pre-wrap">[assistant] {msg.text}</div>
      {:else if msg.type === 'user'}
        <div class="px-2 py-1 text-muted-foreground italic">[user] {msg.text}</div>
      {:else if msg.type === 'result'}
        <div class="px-2 py-1 text-green-700">[result] {msg.text}</div>
      {/if}
    {/each}
    {#if agent.status === 'running'}
      <div class="px-2 py-1 text-blue-500 animate-pulse">[status] Thinking...</div>
    {/if}
  </div>

  <!-- WS input (only for WebSocket agents) -->
  {#if agent.commType === 'ws'}
    <div class="flex gap-2">
      <input
        type="text"
        bind:value={inputText}
        placeholder="Send a message..."
        class="flex-1 rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-ring"
      />
      <Button size="sm" variant="default" disabled={!inputText.trim() || agent.status !== 'running'}>
        Send
      </Button>
    </div>
  {/if}
</div>
