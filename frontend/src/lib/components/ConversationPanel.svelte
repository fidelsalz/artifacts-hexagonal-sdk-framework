<script lang="ts">
  import { onMount, onDestroy, tick } from 'svelte';
  import { API_BASE_URL } from '$lib/config.js';
  import { pushConvMessage, setAgentStatus } from '$lib/stores/caseStore.svelte.js';
  import FolderExplorer from './FolderExplorer.svelte';

  type Msg = Record<string, any>;
  type AgentConfig = {
    id: string;
    label: string;
    commType: 'ws' | 'sse';
    status: 'idle' | 'running' | 'done' | 'error';
    messages: Msg[];
    changedPaths?: Set<string>;
  };

  let { agent }: { agent: AgentConfig } = $props();

  let agentPaths  = $state<{ cwd: string; coding_dir: string | null } | null>(null);
  let inputText   = $state('');
  let ws          = $state<WebSocket | null>(null);
  let connected   = $state(false);
  let thinking    = $state(false);
  let turnCount   = $state(0);
  let sessionInfo = $state<{ model: string; session_id: string } | null>(null);
  let error       = $state('');
  let chatEl      = $state<HTMLElement | null>(null);

  // Fetch agent paths once on mount (agent.id is fixed per panel instance)
  onMount(() => {
    fetch(`${API_BASE_URL}/api/agents/${agent.id}/paths`)
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) agentPaths = data; })
      .catch(() => {});
  });

  // Auto-scroll whenever messages or thinking state change
  $effect(() => {
    agent.messages; thinking;
    tick().then(() => { if (chatEl) chatEl.scrollTop = chatEl.scrollHeight; });
  });

  onMount(() => connect());
  onDestroy(() => disconnect());

  function connect() {
    const url = API_BASE_URL.replace(/^http/, 'ws') + `/ws/agents/${agent.id}/chat`;
    const socket = new WebSocket(url);
    ws = socket;
    error = '';

    socket.onmessage = (ev) => handle(JSON.parse(ev.data));
    socket.onerror   = ()   => { error = 'Connection error.'; };
    socket.onclose   = ()   => {
      connected = false;
      thinking  = false;
      ws        = null;
      setAgentStatus(agent.id, 'idle');
    };
  }

  function disconnect() {
    ws?.close();
    ws = null; connected = false; thinking = false;
  }

  function push(msg: Msg) {
    pushConvMessage(agent.id, msg);
  }

  function handle(data: Record<string, any>) {
    switch (data.type) {
      case 'connected':
        connected = true;
        setAgentStatus(agent.id, 'running');
        push({ role: 'status', text: 'Session ready.' });
        break;
      case 'system':
        sessionInfo = { model: data.model, session_id: data.session_id ?? '' };
        break;
      case 'assistant':
        thinking = false;
        push({ role: 'assistant', text: data.text });
        break;
      case 'result':
        push({
          role:           'result',
          duration_ms:    data.duration_ms,
          total_cost_usd: data.total_cost_usd,
          num_turns:      data.num_turns,
        });
        break;
      case 'turn_complete':
        thinking = false;
        turnCount++;
        break;
      case 'interrupted':
        thinking = false;
        push({ role: 'status', text: 'Interrupted.' });
        break;
      case 'session_reset':
        sessionInfo = null;
        turnCount   = 0;
        push({ role: 'status', text: '— New session started —' });
        break;
      case 'error':
        thinking = false;
        error = data.message ?? 'Unknown error';
        break;
    }
  }

  function send() {
    const text = inputText.trim();
    if (!text || !ws || !connected || thinking) return;
    push({ role: 'user', text });
    inputText = '';
    thinking  = true;
    ws.send(JSON.stringify({ type: 'message', text }));
  }

  function interrupt() {
    ws?.send(JSON.stringify({ type: 'interrupt' }));
  }

  function newSession() {
    push({ role: 'status', text: '— Resetting session… —' });
    ws?.send(JSON.stringify({ type: 'new_session' }));
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  }
</script>

<div class="grid grid-cols-[2fr_1fr] gap-4 items-start">

<!-- ── LEFT: conversation ── -->
<div class="flex flex-col rounded-lg border bg-white overflow-hidden h-[calc(100vh-220px)] min-h-[500px]">

  <!-- ── Title / status bar ── -->
  <div class="flex items-center gap-3 px-4 py-3 bg-zinc-100 border-b shrink-0">
    <div class="flex-1 min-w-0">
      <p class="text-sm font-semibold text-zinc-900">{agent.label}</p>
      {#if sessionInfo}
        <p class="text-[10px] text-zinc-500 font-mono mt-0.5">
          {sessionInfo.model} · {sessionInfo.session_id.slice(0, 8)}
        </p>
      {/if}
    </div>

    <span class="text-[10px] font-medium px-2 py-0.5 rounded-full border shrink-0
                 {thinking   ? 'bg-blue-100  text-blue-700  border-blue-200  animate-pulse'
                : connected  ? 'bg-green-100 text-green-700 border-green-200'
                             : 'bg-zinc-200  text-zinc-500  border-zinc-300'}">
      {thinking ? '● thinking' : connected ? '● connected' : 'connecting…'}
    </span>

    {#if turnCount > 0}
      <span class="text-[10px] text-zinc-400 shrink-0">turn {turnCount}</span>
    {/if}

    <button
      onclick={newSession}
      disabled={!connected}
      class="text-[11px] px-2 py-0.5 rounded border font-medium transition-colors
             {connected
               ? 'border-zinc-300 text-zinc-600 hover:bg-zinc-200'
               : 'border-zinc-200 text-zinc-300 cursor-not-allowed'}"
    >New session</button>

    <button
      onclick={() => { disconnect(); setTimeout(connect, 100); }}
      class="text-[11px] px-2 py-0.5 rounded border border-zinc-300 text-zinc-600 hover:bg-zinc-200 transition-colors"
      title="Reconnect"
    >↻</button>
  </div>

  <!-- ── Messages ── -->
  <div bind:this={chatEl} class="flex-1 overflow-y-auto p-4 flex flex-col gap-3 bg-white">

    {#if agent.messages.length === 0}
      <p class="text-sm text-zinc-400 italic text-center mt-10">
        {connected ? 'Start the conversation below.' : 'Connecting…'}
      </p>
    {/if}

    {#each agent.messages as msg}
      {#if msg.role === 'user'}
        <div class="flex justify-end">
          <div class="max-w-[75%] rounded-2xl rounded-tr-sm bg-zinc-800 text-white px-4 py-2 text-sm whitespace-pre-wrap">
            {msg.text}
          </div>
        </div>

      {:else if msg.role === 'assistant'}
        <div class="flex justify-start">
          <div class="max-w-[75%] rounded-2xl rounded-tl-sm border border-zinc-200 bg-zinc-50 text-zinc-900 px-4 py-2 text-sm whitespace-pre-wrap">
            {msg.text}
          </div>
        </div>

      {:else if msg.role === 'result'}
        <div class="flex justify-center">
          <span class="text-[10px] text-zinc-400 font-mono bg-zinc-100 border border-zinc-200 rounded px-2 py-0.5">
            {(msg.duration_ms / 1000).toFixed(1)}s · ${msg.total_cost_usd.toFixed(6)} · {msg.num_turns} turns
          </span>
        </div>

      {:else if msg.role === 'status'}
        <div class="flex justify-center">
          <p class="text-[10px] text-zinc-400 italic">{msg.text}</p>
        </div>
      {/if}
    {/each}

    {#if thinking}
      <div class="flex justify-start">
        <div class="rounded-2xl rounded-tl-sm border border-zinc-200 bg-zinc-50 px-4 py-2 text-sm text-zinc-400 animate-pulse">
          thinking…
        </div>
      </div>
    {/if}

  </div>

  <!-- ── Error bar ── -->
  {#if error}
    <div class="px-4 py-2 border-t bg-red-50 text-red-600 text-xs shrink-0">{error}</div>
  {/if}

  <!-- ── Input bar ── -->
  <div class="flex items-end gap-2 px-4 py-3 bg-zinc-100 border-t shrink-0">
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <textarea
      bind:value={inputText}
      onkeydown={onKeydown}
      placeholder={connected ? 'Type a message… (Enter to send, Shift+Enter for newline)' : 'Connecting…'}
      disabled={!connected || thinking}
      rows={2}
      class="flex-1 resize-none rounded-lg border border-zinc-300 bg-white text-zinc-900
             placeholder:text-zinc-400 px-3 py-2 text-sm focus:outline-none focus:ring-2
             focus:ring-zinc-400 disabled:opacity-50"
    ></textarea>

    <div class="flex flex-col gap-1.5 shrink-0">
      <button
        onclick={send}
        disabled={!inputText.trim() || !connected || thinking}
        class="px-3 py-1.5 text-xs rounded font-medium transition-colors
               {inputText.trim() && connected && !thinking
                 ? 'bg-zinc-800 text-white hover:bg-zinc-700'
                 : 'bg-zinc-200 text-zinc-400 cursor-not-allowed'}"
      >Send</button>

      <button
        onclick={interrupt}
        disabled={!thinking}
        class="px-3 py-1.5 text-xs rounded font-medium transition-colors
               {thinking
                 ? 'bg-red-600 text-white hover:bg-red-500'
                 : 'bg-zinc-200 text-zinc-400 cursor-not-allowed'}"
      >Stop</button>
    </div>
  </div>

</div>

<!-- ── RIGHT: folder explorer ── -->
<div class="min-w-0">
  {#if agentPaths}
    <FolderExplorer
      shortcuts={[
        ...(agentPaths.coding_dir ? [{ label: 'src', path: agentPaths.coding_dir }] : []),
        { label: 'cwd', path: agentPaths.cwd },
      ]}
      initialPath={agentPaths.coding_dir ?? agentPaths.cwd}
      changedPaths={agent.changedPaths}
    />
  {:else}
    <div class="rounded-md border bg-muted/20 p-3 text-xs text-muted-foreground italic">Loading files…</div>
  {/if}
</div>

</div>
