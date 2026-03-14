<script lang="ts">
  import { API_BASE_URL } from '$lib/config.js';

  type Status = 'idle' | 'running' | 'completed' | 'error';

  type SystemInfo = {
    uuid: string; model: string; session_id: string;
    cwd: string; permission_mode: string; tools_count: number;
  };

  type AgentMessage = { type: 'assistant' | 'user' | 'status'; text?: string };

  type ResultInfo = {
    session_id: string; duration_ms: number; num_turns: number;
    total_cost_usd: number; input_tokens: number; output_tokens: number;
    cache_read_tokens: number;
  };

  let status = $state<Status>('idle');
  let systemInfo = $state<SystemInfo | null>(null);
  let messages = $state<AgentMessage[]>([]);
  let result = $state<ResultInfo | null>(null);
  let errorMsg = $state<string | null>(null);

  let evtSource: EventSource | null = null;

  function runAgent() {
    if (evtSource) evtSource.close();
    systemInfo = null;
    messages = [];
    result = null;
    errorMsg = null;
    status = 'running';

    evtSource = new EventSource(`${API_BASE_URL}/api/agents/sample/stream`);

    evtSource.onmessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data);

      if (data.type === 'system') {
        systemInfo = data;
      } else if (data.type === 'status') {
        messages = [...messages, { type: 'status', text: data.message }];
      } else if (data.type === 'assistant') {
        messages = [...messages, { type: 'assistant', text: data.text }];
      } else if (data.type === 'user') {
        messages = [...messages, { type: 'user' }];
      } else if (data.type === 'result') {
        result = data;
      } else if (data.type === 'done') {
        evtSource?.close();
        evtSource = null;
        status = 'completed';
      } else if (data.type === 'error') {
        errorMsg = data.message;
        evtSource?.close();
        evtSource = null;
        status = 'error';
      }
    };

    evtSource.onerror = () => {
      if (status === 'running') {
        errorMsg = 'Connection lost.';
        status = 'error';
      }
      evtSource?.close();
      evtSource = null;
    };
  }

  function clearOutput() {
    if (evtSource) { evtSource.close(); evtSource = null; }
    systemInfo = null;
    messages = [];
    result = null;
    errorMsg = null;
    status = 'idle';
  }

  const statusLabel: Record<Status, string> = {
    idle: 'Idle',
    running: 'Running...',
    completed: 'Completed',
    error: 'Error',
  };

  const statusColor: Record<Status, string> = {
    idle: 'bg-gray-100 text-gray-600',
    running: 'bg-blue-100 text-blue-700 animate-pulse',
    completed: 'bg-green-100 text-green-700',
    error: 'bg-red-100 text-red-700',
  };
</script>

<div class="max-w-3xl mx-auto">
  <h1 class="text-2xl font-bold mb-6">Agent Runner</h1>

  <!-- Controls -->
  <div class="flex items-center gap-3 mb-6">
    <button
      onclick={runAgent}
      disabled={status === 'running'}
      class="px-4 py-2 bg-blue-600 text-white rounded disabled:bg-gray-300 disabled:cursor-not-allowed hover:bg-blue-700"
    >
      {status === 'running' ? 'Running...' : 'Run Agent'}
    </button>
    <button
      onclick={clearOutput}
      disabled={status === 'running'}
      class="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      Clear
    </button>
    <span class="px-2 py-1 rounded text-sm font-medium {statusColor[status]}">
      {statusLabel[status]}
    </span>
  </div>

  <!-- System Info -->
  {#if systemInfo}
    <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4 text-sm font-mono">
      <p class="font-semibold text-gray-500 mb-2 uppercase text-xs tracking-wide">Session</p>
      <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-gray-700">
        <span class="text-gray-400">Model</span><span>{systemInfo.model}</span>
        <span class="text-gray-400">Session</span><span class="truncate">{systemInfo.session_id}</span>
        <span class="text-gray-400">Permission</span><span>{systemInfo.permission_mode}</span>
        <span class="text-gray-400">Tools</span><span>{systemInfo.tools_count}</span>
      </div>
    </div>
  {/if}

  <!-- Message Stream -->
  {#if messages.length > 0 || status === 'running'}
    <div class="border border-gray-200 rounded-lg divide-y divide-gray-100 mb-4">
      {#each messages as msg, i}
        {#if msg.type === 'status'}
          <div class="p-2 text-xs text-gray-400 italic">{msg.text}</div>
        {:else if msg.type === 'assistant'}
          <div class="p-3 text-sm text-gray-800 whitespace-pre-wrap">{msg.text}</div>
        {:else if msg.type === 'user'}
          <div class="p-2 text-xs text-gray-400 italic">— user turn —</div>
        {/if}
      {/each}
      {#if status === 'running'}
        <div class="p-3 text-xs text-blue-400 animate-pulse">Agent is thinking...</div>
      {/if}
    </div>
  {/if}

  <!-- Error -->
  {#if errorMsg}
    <div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4 text-sm text-red-700">
      {errorMsg}
    </div>
  {/if}

  <!-- Result Summary -->
  {#if result}
    <div class="bg-green-50 border border-green-200 rounded-lg p-4 text-sm font-mono">
      <p class="font-semibold text-gray-500 mb-2 uppercase text-xs tracking-wide">Result</p>
      <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-gray-700">
        <span class="text-gray-400">Duration</span><span>{(result.duration_ms / 1000).toFixed(2)}s</span>
        <span class="text-gray-400">Turns</span><span>{result.num_turns}</span>
        <span class="text-gray-400">Cost</span><span>${result.total_cost_usd.toFixed(6)}</span>
        <span class="text-gray-400">Input tokens</span><span>{result.input_tokens.toLocaleString()}</span>
        <span class="text-gray-400">Output tokens</span><span>{result.output_tokens.toLocaleString()}</span>
        <span class="text-gray-400">Cache read</span><span>{result.cache_read_tokens.toLocaleString()}</span>
      </div>
    </div>
  {/if}

  <!-- Empty state -->
  {#if status === 'idle' && !systemInfo && messages.length === 0}
    <p class="text-gray-400 text-sm">Click "Run Agent" to start.</p>
  {/if}
</div>
