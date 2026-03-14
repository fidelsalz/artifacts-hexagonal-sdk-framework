<script lang="ts">
  import { onDestroy, tick } from 'svelte';
  import { Dialog as DialogPrimitive } from 'bits-ui';
  import * as Dialog from '$lib/components/ui/dialog/index.js';
  import { API_BASE_URL } from '$lib/config.js';

  type UserMsg     = { role: 'user';      text: string };
  type AssistMsg   = { role: 'assistant'; text: string };
  type ResultMsg   = { role: 'result';    duration_ms: number; total_cost_usd: number; num_turns: number };
  type StatusMsg   = { role: 'status';    text: string };
  type ConvMsg = UserMsg | AssistMsg | ResultMsg | StatusMsg;

  let {
    agentId,
    agentLabel,
    open,
    onclose,
  }: {
    agentId:    string;
    agentLabel: string;
    open:       boolean;
    onclose:    () => void;
  } = $props();

  let messages    = $state<ConvMsg[]>([]);
  let inputText   = $state('');
  let ws          = $state<WebSocket | null>(null);
  let connected   = $state(false);
  let thinking    = $state(false);
  let turnCount   = $state(0);
  let sessionInfo = $state<{ model: string; session_id: string } | null>(null);
  let error       = $state('');
  let chatEl      = $state<HTMLElement | null>(null);

  // Connect on open, disconnect on close
  $effect(() => {
    if (open) {
      if (!ws) connect();
    } else {
      disconnect();
    }
  });

  // Auto-scroll on new messages
  $effect(() => {
    messages; thinking;
    tick().then(() => { if (chatEl) chatEl.scrollTop = chatEl.scrollHeight; });
  });

  function wsUrl() {
    return API_BASE_URL.replace(/^http/, 'ws') + `/ws/agents/${agentId}/chat`;
  }

  function connect() {
    const socket = new WebSocket(wsUrl());
    ws = socket;
    error = '';

    socket.onmessage = (ev) => handle(JSON.parse(ev.data));
    socket.onerror   = ()   => { error = 'Connection error'; };
    socket.onclose   = ()   => { connected = false; thinking = false; ws = null; };
  }

  function disconnect() {
    ws?.close();
    ws = null; connected = false; thinking = false;
  }

  function handle(data: Record<string, any>) {
    switch (data.type) {
      case 'connected':
        connected = true;
        messages = [...messages, { role: 'status', text: 'Session ready.' }];
        break;
      case 'system':
        sessionInfo = { model: data.model, session_id: data.session_id ?? '' };
        break;
      case 'assistant':
        thinking = false;
        messages = [...messages, { role: 'assistant', text: data.text }];
        break;
      case 'result':
        messages = [...messages, {
          role: 'result',
          duration_ms:    data.duration_ms,
          total_cost_usd: data.total_cost_usd,
          num_turns:      data.num_turns,
        }];
        break;
      case 'turn_complete':
        thinking = false;
        turnCount++;
        break;
      case 'interrupted':
        thinking = false;
        messages = [...messages, { role: 'status', text: 'Interrupted.' }];
        break;
      case 'session_reset':
        sessionInfo = null;
        turnCount = 0;
        messages = [...messages, { role: 'status', text: '— New session started —' }];
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
    messages  = [...messages, { role: 'user', text }];
    inputText = '';
    thinking  = true;
    ws.send(JSON.stringify({ type: 'message', text }));
  }

  function interrupt() {
    ws?.send(JSON.stringify({ type: 'interrupt' }));
  }

  function newSession() {
    messages = [...messages, { role: 'status', text: '— Resetting session… —' }];
    ws?.send(JSON.stringify({ type: 'new_session' }));
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  }

  function tryClose() { disconnect(); onclose(); }

  onDestroy(() => disconnect());
</script>

<Dialog.Root open={open} onOpenChange={(o) => { if (!o) tryClose(); }}>
  <Dialog.Portal>
    <Dialog.Overlay />
    <DialogPrimitive.Content
      data-slot="dialog-content"
      class="bg-background fixed top-1/2 left-1/2 z-50 -translate-x-1/2 -translate-y-1/2
             flex flex-col rounded-lg border shadow-lg duration-200
             data-[state=open]:animate-in data-[state=closed]:animate-out
             data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0
             data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95
             w-[80vw] max-w-[900px] h-[80vh]"
    >

      <!-- ── Title bar ── -->
      <div class="flex items-center gap-3 px-4 py-3 bg-zinc-100 border-b rounded-t-lg shrink-0">
        <div class="flex-1 min-w-0">
          <Dialog.Title class="text-sm font-semibold text-zinc-900">{agentLabel}</Dialog.Title>
          {#if sessionInfo}
            <p class="text-[10px] text-zinc-500 font-mono mt-0.5">
              {sessionInfo.model} · {sessionInfo.session_id.slice(0, 8)}
            </p>
          {/if}
        </div>

        <!-- Status badge -->
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
          onclick={tryClose}
          class="px-2 py-1 rounded text-xs font-bold text-zinc-400 hover:bg-zinc-200 hover:text-zinc-700 transition-colors"
        >✕</button>
      </div>

      <!-- ── Chat messages ── -->
      <div bind:this={chatEl} class="flex-1 overflow-y-auto p-4 flex flex-col gap-3 min-h-0 bg-white">

        {#if messages.length === 0}
          <p class="text-sm text-zinc-400 italic text-center mt-8">
            {connected ? 'Start the conversation below.' : 'Connecting…'}
          </p>
        {/if}

        {#each messages as msg}
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
      <div class="flex items-end gap-2 px-4 py-3 bg-zinc-100 border-t rounded-b-lg shrink-0">
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

          <button
            onclick={newSession}
            disabled={!connected}
            class="px-3 py-1.5 text-xs rounded font-medium border transition-colors
                   {connected
                     ? 'border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-50'
                     : 'bg-zinc-200 text-zinc-400 cursor-not-allowed border-transparent'}"
          >New</button>
        </div>
      </div>

    </DialogPrimitive.Content>
  </Dialog.Portal>
</Dialog.Root>
