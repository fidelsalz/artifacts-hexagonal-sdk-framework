<script lang="ts">
  import { Button } from '$lib/components/ui/button';
  import { Separator } from '$lib/components/ui/separator';
  import { runAgent, stopAgent } from '$lib/stores/caseStore.svelte.js';
  import { API_BASE_URL } from '$lib/config.js';
  import FolderExplorer from './FolderExplorer.svelte';

  type Msg = Record<string, any>;
  type RunBlock = {
    runStart:      Msg;
    system:        Msg | null;
    result:        Msg | null;
    statusMsgs:    Msg[];
    assistantMsgs: Msg[];
  };

  type AgentConfig = {
    id: string;
    label: string;
    commType: 'sse';
    status: 'idle' | 'running' | 'done' | 'error';
    messages: Msg[];
    changedPaths?: Set<string>;
  };

  let { agent, validator }: { agent: AgentConfig; validator: AgentConfig } = $props();

  let agentPaths = $state<{ cwd: string; coding_dir: string | null } | null>(null);

  $effect(() => {
    const id = agent.id;          // tracked — re-runs whenever the agent changes
    agentPaths = null;            // reset so FolderExplorer unmounts/remounts clean
    fetch(`${API_BASE_URL}/api/agents/${id}/paths`)
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) agentPaths = data; })
      .catch(() => {});
  });

  const pairStatus = $derived(
    agent.status === 'running' || validator.status === 'running' ? 'running'
    : agent.status === 'error'  || validator.status === 'error'  ? 'error'
    : agent.status === 'done'   && validator.status === 'done'   ? 'done'
    : 'idle'
  );

  const statusColor: Record<string, string> = {
    idle:    'bg-gray-100 text-gray-600',
    running: 'bg-blue-100 text-blue-700 animate-pulse',
    done:    'bg-green-100 text-green-700',
    error:   'bg-red-100 text-red-700',
  };

  function fmtTime(iso: string): string {
    return new Date(iso).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  /** Returns true for status messages that are lifecycle announcements
   *  ("Starting X", "X Finished") — already shown in the Row 1 headline. */
  function isLifecycleStatus(text: string): boolean {
    const t = text.trim();
    return (
      /^starting\b/i.test(t)  ||   // "Starting Ports Developer"
      /\bfinished\b/i.test(t) ||   // "Ports Developer Finished"
      /^\[.+\]/i.test(t)           // "[Ports Validator] Starting validation..." etc.
    );
  }

  /** Group messages into per-run blocks.
   *  Each block owns its status, system, result, and assistant messages.
   *  Row 1 = status bar   Row 2 = session+result   Row 3 = assistant text */
  function buildRuns(messages: Msg[]): RunBlock[] {
    const runs: RunBlock[] = [];
    let i = 0;
    while (i < messages.length) {
      if (messages[i].type !== 'run-start') { i++; continue; }
      const runStart = messages[i];
      let system: Msg | null = null;
      let result: Msg | null = null;
      const statusMsgs: Msg[] = [];
      const assistantMsgs: Msg[] = [];
      let j = i + 1;
      while (j < messages.length && messages[j].type !== 'run-start') {
        const m = messages[j];
        if      (m.type === 'system')    system = m;
        else if (m.type === 'result')    result = m;
        else if (m.type === 'status' && !isLifecycleStatus(m.text)) statusMsgs.push(m);
        else if (m.type === 'assistant') assistantMsgs.push(m);
        j++;
      }
      runs.push({ runStart, system, result, statusMsgs, assistantMsgs });
      i = j;
    }
    return runs;
  }

  const agentRuns     = $derived(buildRuns(agent.messages));
  const validatorRuns = $derived(buildRuns(validator.messages));
</script>

<!-- Indigo left-border accent marks this as a coding agent panel -->
<div class="rounded-lg border border-l-4 border-l-indigo-400 bg-card p-4">

  <!-- Header -->
  <div class="flex items-center justify-between mb-3">
    <div class="flex items-center gap-2">
      <span class="font-semibold text-sm">{agent.label}</span>
      <span class="text-xs font-medium px-2 py-0.5 rounded-full border bg-sky-100 text-sky-700 border-sky-200">SSE</span>
    </div>
    <span class="text-xs font-medium px-2 py-0.5 rounded-full {statusColor[pairStatus]}">
      {pairStatus === 'running' ? '● ACTIVE' : pairStatus.toUpperCase()}
    </span>
  </div>

  <Separator class="mb-3" />

  <!-- Run / Stop -->
  <div class="flex gap-2 mb-3">
    <Button size="sm" variant="default" onclick={() => runAgent(agent.id)}  disabled={pairStatus === 'running'}>Run</Button>
    <Button size="sm" variant="outline" onclick={() => stopAgent(agent.id)} disabled={pairStatus !== 'running'}>Stop</Button>
  </div>

  <!-- Two-column layout: left = output (wider), right = files -->
  <div class="grid grid-cols-[2fr_1fr] gap-4 items-start">

    <!-- ── LEFT ── -->
    <div class="flex flex-col gap-4 min-w-0">

      {#if agentRuns.length > 0 || agent.status === 'running'}

        {#each agentRuns as run, ri}
          <div class="flex flex-col gap-2">

            <!-- ── ROW 1: status bar ── -->
            <div class="rounded border bg-muted/40 px-3 py-2 flex flex-col gap-1">

              <!-- Starting / Finished headline -->
              <div class="flex items-center gap-2 text-xs">
                <span class="text-blue-400">▶</span>
                <span class="font-medium text-foreground">Starting...</span>
                {#if run.runStart.timestamp}
                  <span class="text-[10px] text-muted-foreground">{fmtTime(run.runStart.timestamp)}</span>
                {/if}
                {#if run.result}
                  <span class="ml-auto flex items-center gap-1.5 text-xs">
                    <span class="text-green-500">✓</span>
                    <span class="font-medium text-green-700">Finished</span>
                    <span class="text-[10px] text-muted-foreground">{(run.result.duration_ms / 1000).toFixed(1)}s</span>
                  </span>
                {:else if agent.status === 'running' && ri === agentRuns.length - 1}
                  <span class="ml-auto text-[10px] text-blue-500 animate-pulse">running…</span>
                {/if}
              </div>

              <!-- Live status / rollback / clear messages -->
              {#each run.statusMsgs as sm}
                <p class="text-[11px] text-muted-foreground italic pl-4">→ {sm.text}</p>
              {/each}

            </div>

            <!-- ── ROW 2: session + result ── -->
            {#if run.system || run.result}
              <div class="flex gap-2">
                {#if run.system}
                  <div class="flex-1 min-w-0 rounded border bg-muted/50 px-2 py-1.5 text-[11px] font-mono">
                    <div class="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5 text-foreground">
                      <span class="text-muted-foreground">Model</span><span class="truncate">{run.system.model}</span>
                      <span class="text-muted-foreground">CWD</span><span class="truncate">{run.system.cwd}</span>
                      <span class="text-muted-foreground">Mode</span><span>{run.system.permission_mode}</span>
                      <span class="text-muted-foreground">Tools</span><span>{run.system.tools_count}</span>
                    </div>
                  </div>
                {/if}
                {#if run.result}
                  <div class="flex-1 min-w-0 rounded border border-green-200 bg-green-50 px-2 py-1.5 text-[11px] font-mono">
                    <div class="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5 text-foreground">
                      <span class="text-muted-foreground">Turns</span><span>{run.result.num_turns}</span>
                      <span class="text-muted-foreground">Cost</span><span>${run.result.total_cost_usd.toFixed(6)}</span>
                      <span class="text-muted-foreground">In</span><span>{run.result.input_tokens.toLocaleString()} tok</span>
                      <span class="text-muted-foreground">Out</span><span>{run.result.output_tokens.toLocaleString()} tok</span>
                      <span class="text-muted-foreground">Cache</span><span>{run.result.cache_read_tokens.toLocaleString()} tok</span>
                    </div>
                  </div>
                {/if}
              </div>
            {/if}

            <!-- ── ROW 3: assistant messages ── -->
            {#each run.assistantMsgs as am}
              <div class="rounded-md border bg-background px-3 py-2 text-sm text-foreground whitespace-pre-wrap">{am.text}</div>
            {/each}

          </div>
        {/each}

      {:else}
        <p class="text-sm text-muted-foreground italic">Click Run to start.</p>
      {/if}

      <!-- ── Validator ── -->
      {#if validatorRuns.length > 0 || validator.status === 'running'}
        <div class="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-widest text-amber-600">
          <div class="flex-1 border-t border-amber-200"></div>
          <span>Validator</span>
          <div class="flex-1 border-t border-amber-200"></div>
        </div>

        {#each validatorRuns as run, ri}
          <div class="flex flex-col gap-2">

            <!-- Row 1 -->
            <div class="rounded border bg-muted/40 px-3 py-2 flex flex-col gap-1">
              <div class="flex items-center gap-2 text-xs">
                <span class="text-amber-400">▶</span>
                <span class="font-medium text-foreground">Starting...</span>
                {#if run.runStart.timestamp}
                  <span class="text-[10px] text-muted-foreground">{fmtTime(run.runStart.timestamp)}</span>
                {/if}
                {#if run.result}
                  <span class="ml-auto flex items-center gap-1.5 text-xs">
                    <span class="text-green-500">✓</span>
                    <span class="font-medium text-green-700">Finished</span>
                    <span class="text-[10px] text-muted-foreground">{(run.result.duration_ms / 1000).toFixed(1)}s</span>
                  </span>
                {:else if validator.status === 'running' && ri === validatorRuns.length - 1}
                  <span class="ml-auto text-[10px] text-amber-500 animate-pulse">running…</span>
                {/if}
              </div>
              {#each run.statusMsgs as sm}
                <p class="text-[11px] text-muted-foreground italic pl-4">→ {sm.text}</p>
              {/each}
            </div>

            <!-- Row 2 -->
            {#if run.system || run.result}
              <div class="flex gap-2">
                {#if run.system}
                  <div class="flex-1 min-w-0 rounded border bg-muted/50 px-2 py-1.5 text-[11px] font-mono">
                    <div class="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5">
                      <span class="text-muted-foreground">Model</span><span class="truncate">{run.system.model}</span>
                      <span class="text-muted-foreground">Mode</span><span>{run.system.permission_mode}</span>
                    </div>
                  </div>
                {/if}
                {#if run.result}
                  <div class="flex-1 min-w-0 rounded border border-green-200 bg-green-50 px-2 py-1.5 text-[11px] font-mono">
                    <div class="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5">
                      <span class="text-muted-foreground">Cost</span><span>${run.result.total_cost_usd.toFixed(6)}</span>
                      <span class="text-muted-foreground">Out</span><span>{run.result.output_tokens.toLocaleString()} tok</span>
                    </div>
                  </div>
                {/if}
              </div>
            {/if}

            <!-- Row 3 -->
            {#each run.assistantMsgs as am}
              <div class="rounded-md border border-amber-100 bg-amber-50/40 px-3 py-2 text-sm text-foreground whitespace-pre-wrap">{am.text}</div>
            {/each}

          </div>
        {/each}

      {/if}

    </div>

    <!-- ── RIGHT: folder explorer ── -->
    <div class="min-w-0">
      {#if agentPaths}
        <FolderExplorer
          shortcuts={[
            ...(agentPaths.coding_dir ? [{ label: 'coding dir', path: agentPaths.coding_dir }] : []),
            { label: 'cwd', path: agentPaths.cwd },
          ]}
          initialPath={agentPaths.cwd}
          changedPaths={agent.changedPaths}
        />
      {:else}
        <div class="rounded-md border bg-muted/20 p-3 text-xs text-muted-foreground italic">Loading files…</div>
      {/if}
    </div>

  </div>

</div>
