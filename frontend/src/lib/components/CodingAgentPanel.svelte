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
    const id = agent.id;
    agentPaths = null;
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

  function fmtDuration(ms: number): string {
    const s = Math.round(ms / 1000);
    return s >= 60 ? `${Math.floor(s / 60)}m ${s % 60}s` : `${s}s`;
  }

  /** Compute finish timestamp from run-start + duration_ms. */
  function finishTime(runStart: Msg, result: Msg | null): string | null {
    if (!result?.duration_ms || !runStart.timestamp) return null;
    return fmtTime(new Date(new Date(runStart.timestamp).getTime() + result.duration_ms).toISOString());
  }

  function isLifecycleStatus(text: string): boolean {
    const t = text.trim();
    return (
      /^starting\b/i.test(t)  ||
      /\bfinished\b/i.test(t) ||
      /^\[.+\]/i.test(t)
    );
  }

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
  const totalRuns     = $derived(Math.max(agentRuns.length, validatorRuns.length));
  const runIndices    = $derived(Array.from({ length: totalRuns }, (_, i) => i));

  // Track which run blocks are collapsed (by index).
  // Auto-collapse all-but-last when a new run starts.
  let collapsedRuns = $state<Set<number>>(new Set());
  let _prevCount = 0;

  $effect(() => {
    const count = agentRuns.length; // reactive
    if (count !== _prevCount) {
      if (count > 1) {
        const next = new Set<number>();
        for (let i = 0; i < count - 1; i++) next.add(i);
        collapsedRuns = next;
      }
      _prevCount = count;
    }
  });

  function toggleRun(i: number) {
    const next = new Set(collapsedRuns);
    if (next.has(i)) next.delete(i); else next.add(i);
    collapsedRuns = next;
  }
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
    <div class="flex flex-col gap-2 min-w-0">

      {#if totalRuns > 0}

        {#each runIndices as ri}
          {@const aRun = agentRuns[ri] ?? null}
          {@const vRun = validatorRuns[ri] ?? null}
          {@const isLastAgentRun    = ri === agentRuns.length - 1}
          {@const isLastValidatorRun = ri === validatorRuns.length - 1}
          {@const collapsed = collapsedRuns.has(ri)}
          {@const agentRunning    = agent.status     === 'running' && isLastAgentRun}
          {@const validatorRunning = validator.status === 'running' && isLastValidatorRun}
          {@const agentFinish    = aRun ? finishTime(aRun.runStart, aRun.result) : null}
          {@const validatorFinish = vRun ? finishTime(vRun.runStart, vRun.result) : null}

          <div class="rounded-lg border border-zinc-200 overflow-hidden">

            <!-- ── Collapsible header ── -->
            <button
              class="w-full flex items-center gap-1.5 px-3 py-2 bg-zinc-50 hover:bg-zinc-100 text-[11px] text-left transition-colors select-none"
              onclick={() => toggleRun(ri)}
            >
              <!-- Iteration number -->
              <span class="font-mono font-bold text-zinc-400 min-w-[1.5rem]">#{ri + 1}</span>

              <!-- Agent timing -->
              <span class="text-blue-400 font-bold">▶</span>
              {#if aRun}
                <span class="font-mono text-zinc-600">{fmtTime(aRun.runStart.timestamp)}</span>
                {#if agentFinish}
                  <span class="text-zinc-400">→</span>
                  <span class="font-mono text-green-700">{agentFinish}</span>
                  <span class="text-zinc-400">({fmtDuration(aRun.result!.duration_ms)})</span>
                {:else if agentRunning}
                  <span class="text-zinc-400">→</span>
                  <span class="text-blue-500 animate-pulse">running…</span>
                {/if}
              {:else if agentRunning}
                <span class="text-blue-500 animate-pulse">running…</span>
              {/if}

              <!-- Validator timing (only when it exists or is running) -->
              {#if vRun || validatorRunning}
                <span class="text-zinc-300 mx-0.5">│</span>
                <span class="text-amber-500 font-bold">◈</span>
                {#if vRun}
                  <span class="font-mono text-zinc-600">{fmtTime(vRun.runStart.timestamp)}</span>
                  {#if validatorFinish}
                    <span class="text-zinc-400">→</span>
                    <span class="font-mono text-green-700">{validatorFinish}</span>
                  {:else if validatorRunning}
                    <span class="text-zinc-400">→</span>
                    <span class="text-amber-500 animate-pulse">running…</span>
                  {/if}
                {:else if validatorRunning}
                  <span class="text-amber-500 animate-pulse">running…</span>
                {/if}
              {/if}

              <!-- Right side: status chip + chevron -->
              <span class="ml-auto flex items-center gap-2">
                {#if agentRunning || validatorRunning}
                  <span class="text-blue-500 animate-pulse">● active</span>
                {:else if aRun?.result && vRun?.result}
                  <span class="text-green-600">✓ done</span>
                {:else if aRun?.result}
                  <span class="text-zinc-500">agent done</span>
                {/if}
                <span class="text-zinc-400 text-[10px]">{collapsed ? '▶' : '▼'}</span>
              </span>
            </button>

            <!-- ── Collapsible body ── -->
            {#if !collapsed}
              <div class="flex flex-col gap-3 px-3 py-3 border-t border-zinc-100">

                <!-- ── Agent section ── -->
                {#if aRun}

                  <!-- Status messages (pre-run spread, rollback, etc.) -->
                  {#if aRun.statusMsgs.length > 0}
                    <div class="rounded border bg-muted/40 px-3 py-2 flex flex-col gap-0.5">
                      {#each aRun.statusMsgs as sm}
                        <p class="text-[11px] text-muted-foreground italic">→ {sm.text}</p>
                      {/each}
                    </div>
                  {/if}

                  <!-- System + Result boxes -->
                  {#if aRun.system || aRun.result}
                    <div class="flex gap-2">
                      {#if aRun.system}
                        <div class="flex-1 min-w-0 rounded border bg-muted/50 px-2 py-1.5 text-[11px] font-mono">
                          <div class="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5 text-foreground">
                            <span class="text-muted-foreground">Model</span><span class="truncate">{aRun.system.model}</span>
                            <span class="text-muted-foreground">CWD</span><span class="truncate">{aRun.system.cwd}</span>
                            <span class="text-muted-foreground">Mode</span><span>{aRun.system.permission_mode}</span>
                            <span class="text-muted-foreground">Tools</span><span>{aRun.system.tools_count}</span>
                          </div>
                        </div>
                      {/if}
                      {#if aRun.result}
                        <div class="flex-1 min-w-0 rounded border border-green-200 bg-green-50 px-2 py-1.5 text-[11px] font-mono">
                          <div class="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5 text-foreground">
                            <span class="text-muted-foreground">Turns</span><span>{aRun.result.num_turns}</span>
                            <span class="text-muted-foreground">Cost</span><span>${aRun.result.total_cost_usd.toFixed(6)}</span>
                            <span class="text-muted-foreground">In</span><span>{aRun.result.input_tokens.toLocaleString()} tok</span>
                            <span class="text-muted-foreground">Out</span><span>{aRun.result.output_tokens.toLocaleString()} tok</span>
                            <span class="text-muted-foreground">Cache</span><span>{aRun.result.cache_read_tokens.toLocaleString()} tok</span>
                          </div>
                        </div>
                      {/if}
                    </div>
                  {/if}

                  <!-- Assistant text -->
                  {#each aRun.assistantMsgs as am}
                    <div class="rounded-md border bg-background px-3 py-2 text-sm text-foreground whitespace-pre-wrap">{am.text}</div>
                  {/each}

                {:else if agentRunning}
                  <p class="text-xs text-blue-500 animate-pulse italic px-1">Agent is running…</p>
                {/if}

                <!-- ── Validator section ── -->
                {#if vRun || validatorRunning}

                  <div class="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-widest text-amber-600">
                    <div class="flex-1 border-t border-amber-200"></div>
                    <span>Validator</span>
                    <div class="flex-1 border-t border-amber-200"></div>
                  </div>

                  {#if vRun}

                    <!-- Status messages -->
                    {#if vRun.statusMsgs.length > 0}
                      <div class="rounded border bg-muted/40 px-3 py-2 flex flex-col gap-0.5">
                        {#each vRun.statusMsgs as sm}
                          <p class="text-[11px] text-muted-foreground italic">→ {sm.text}</p>
                        {/each}
                      </div>
                    {/if}

                    <!-- System + Result boxes -->
                    {#if vRun.system || vRun.result}
                      <div class="flex gap-2">
                        {#if vRun.system}
                          <div class="flex-1 min-w-0 rounded border bg-muted/50 px-2 py-1.5 text-[11px] font-mono">
                            <div class="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5">
                              <span class="text-muted-foreground">Model</span><span class="truncate">{vRun.system.model}</span>
                              <span class="text-muted-foreground">Mode</span><span>{vRun.system.permission_mode}</span>
                            </div>
                          </div>
                        {/if}
                        {#if vRun.result}
                          <div class="flex-1 min-w-0 rounded border border-green-200 bg-green-50 px-2 py-1.5 text-[11px] font-mono">
                            <div class="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5">
                              <span class="text-muted-foreground">Cost</span><span>${vRun.result.total_cost_usd.toFixed(6)}</span>
                              <span class="text-muted-foreground">Out</span><span>{vRun.result.output_tokens.toLocaleString()} tok</span>
                            </div>
                          </div>
                        {/if}
                      </div>
                    {/if}

                    <!-- Assistant text -->
                    {#each vRun.assistantMsgs as am}
                      <div class="rounded-md border border-amber-100 bg-amber-50/40 px-3 py-2 text-sm text-foreground whitespace-pre-wrap">{am.text}</div>
                    {/each}

                  {:else}
                    <p class="text-xs text-amber-500 animate-pulse italic px-1">Validator is running…</p>
                  {/if}

                {/if}

              </div>
            {/if}

          </div>
        {/each}

      {:else}
        <p class="text-sm text-muted-foreground italic">Click Run to start.</p>
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
