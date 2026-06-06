<script lang="ts">
	import { API_BASE } from '$lib/config';
	import {
		getSession,
		incrementTurnCount,
		pushMessage,
		removeSession,
		sessionStore,
		setError,
		setSessionInfo,
		setStatus,
	} from '$lib/stores/sessionStore.svelte';
	import { onDestroy, onMount, tick } from 'svelte';

	let { sessionKey }: { sessionKey: string } = $props();

	// Read session reactively from store — Svelte 5 tracks the reads
	const session = $derived(getSession(sessionKey));

	// ---------- ephemeral component-local state ----------
	let ws = $state<WebSocket | null>(null);
	let connected = $state(false);
	let thinking = $state(false);
	let inputText = $state('');
	let chatEl = $state<HTMLElement | null>(null);

	// Auto-scroll on new messages or thinking change
	$effect(() => {
		session?.messages.length;
		thinking;
		tick().then(() => {
			if (chatEl) chatEl.scrollTop = chatEl.scrollHeight;
		});
	});

	onMount(() => connect());
	onDestroy(() => ws?.close());

	function connect() {
		if (!session) return;
		const wsUrl = API_BASE.replace(/^http/, 'ws') + session.wsUrl;
		const socket = new WebSocket(wsUrl);
		ws = socket;
		setStatus(sessionKey, 'connecting');

		socket.onmessage = (ev) => handle(JSON.parse(ev.data));
		socket.onerror = () => {
			setError(sessionKey, 'Connection error.');
			setStatus(sessionKey, 'error');
		};
		socket.onclose = () => {
			connected = false;
			thinking = false;
			ws = null;
			setStatus(sessionKey, 'closed');
		};
	}

	function handle(data: Record<string, unknown>) {
		switch (data.type) {
			case 'connected':
				connected = true;
				setStatus(sessionKey, 'connected');
				pushMessage(sessionKey, { role: 'status', text: 'Session ready — agent running opening task…' });
				break;
			case 'system':
				setSessionInfo(sessionKey, {
					model: String(data.model ?? ''),
					sessionId: String(data.session_id ?? ''),
				});
				break;
			case 'assistant':
				thinking = false;
				setStatus(sessionKey, 'connected');
				pushMessage(sessionKey, { role: 'assistant', text: String(data.text ?? '') });
				break;
			case 'result':
				pushMessage(sessionKey, {
					role: 'result',
					duration_ms: Number(data.duration_ms ?? 0),
					total_cost_usd: Number(data.total_cost_usd ?? 0),
					num_turns: Number(data.num_turns ?? 0),
				});
				break;
			case 'turn_complete':
				thinking = false;
				setStatus(sessionKey, 'connected');
				incrementTurnCount(sessionKey);
				break;
			case 'interrupted':
				thinking = false;
				setStatus(sessionKey, 'connected');
				pushMessage(sessionKey, { role: 'status', text: 'Interrupted.' });
				break;
			case 'session_reset':
				setSessionInfo(sessionKey, null);
				pushMessage(sessionKey, { role: 'status', text: '— New session started —' });
				break;
			case 'error':
				thinking = false;
				setError(sessionKey, String(data.message ?? 'Unknown error'));
				setStatus(sessionKey, 'error');
				break;
		}
	}

	function send() {
		const text = inputText.trim();
		if (!text || !ws || !connected || thinking) return;
		pushMessage(sessionKey, { role: 'user', text });
		inputText = '';
		thinking = true;
		setStatus(sessionKey, 'thinking');
		ws.send(JSON.stringify({ type: 'message', text }));
	}

	function interrupt() {
		ws?.send(JSON.stringify({ type: 'interrupt' }));
	}

	function newSession() {
		pushMessage(sessionKey, { role: 'status', text: '— Resetting session… —' });
		ws?.send(JSON.stringify({ type: 'new_session' }));
	}

	function onKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			send();
		}
	}

	function shortCwd(cwd: string): string {
		const parts = cwd.split('/');
		return parts.slice(-2).join('/');
	}
</script>

{#if session}
	<div class="flex flex-col rounded-lg border border-slate-200 bg-white overflow-hidden h-[520px]">

		<!-- Title bar -->
		<div class="flex items-center gap-2 px-4 py-2.5 bg-slate-50 border-b shrink-0">
			<div class="flex-1 min-w-0">
				<p class="text-sm font-semibold text-slate-900 leading-tight">{session.agentName}</p>
				{#if session.sessionInfo}
					<p class="text-[10px] text-slate-400 font-mono mt-0.5">
						{session.sessionInfo.model} · {session.sessionInfo.sessionId.slice(0, 8)}
					</p>
				{:else}
					<p class="text-[10px] text-slate-400 font-mono mt-0.5">{shortCwd(session.cwd)}</p>
				{/if}
			</div>

			<!-- Status badge -->
			<span class="text-[10px] font-medium px-2 py-0.5 rounded-full border shrink-0
			             {thinking
				             ? 'bg-blue-100 text-blue-700 border-blue-200 animate-pulse'
				             : connected
				               ? 'bg-emerald-100 text-emerald-700 border-emerald-200'
				               : session.status === 'error'
				                 ? 'bg-red-100 text-red-700 border-red-200'
				                 : 'bg-slate-100 text-slate-500 border-slate-200'}">
				{thinking ? '● thinking' : connected ? '● connected' : session.status}
			</span>

			{#if session.turnCount > 0}
				<span class="text-[10px] text-slate-400 shrink-0">turn {session.turnCount}</span>
			{/if}

			<button
				onclick={newSession}
				disabled={!connected}
				class="text-[11px] px-2 py-0.5 rounded border font-medium transition-colors shrink-0
				       {connected ? 'border-slate-300 text-slate-600 hover:bg-slate-200' : 'border-slate-200 text-slate-300 cursor-not-allowed'}"
			>
				New
			</button>

			<button
				onclick={() => { ws?.close(); setTimeout(connect, 100); }}
				title="Reconnect"
				class="text-[11px] px-2 py-0.5 rounded border border-slate-300 text-slate-600 hover:bg-slate-200 transition-colors shrink-0"
			>↻</button>

			<button
				onclick={() => removeSession(sessionKey)}
				title="Close session"
				class="text-[11px] px-2 py-0.5 rounded border border-slate-200 text-slate-400 hover:border-red-300 hover:text-red-600 hover:bg-red-50 transition-colors shrink-0"
			>✕</button>
		</div>

		<!-- Messages -->
		<div bind:this={chatEl} class="flex-1 overflow-y-auto p-4 flex flex-col gap-2.5 bg-white">
			{#if session.messages.length === 0}
				<p class="text-xs text-slate-400 italic text-center mt-8">
					{connected ? 'Agent is working…' : 'Connecting…'}
				</p>
			{/if}

			{#each session.messages as msg}
				{#if msg.role === 'user'}
					<div class="flex justify-end">
						<div class="max-w-[78%] rounded-2xl rounded-tr-sm bg-slate-800 text-white px-4 py-2 text-sm whitespace-pre-wrap">
							{msg.text}
						</div>
					</div>

				{:else if msg.role === 'assistant'}
					<div class="flex justify-start">
						<div class="max-w-[78%] rounded-2xl rounded-tl-sm border border-slate-200 bg-slate-50 text-slate-900 px-4 py-2 text-sm whitespace-pre-wrap">
							{msg.text}
						</div>
					</div>

				{:else if msg.role === 'result'}
					<div class="flex justify-center">
						<span class="text-[10px] text-slate-400 font-mono bg-slate-100 border border-slate-200 rounded px-2 py-0.5">
							{((msg.duration_ms ?? 0) / 1000).toFixed(1)}s · ${(msg.total_cost_usd ?? 0).toFixed(6)} · {msg.num_turns} turns
						</span>
					</div>

				{:else if msg.role === 'status'}
					<div class="flex justify-center">
						<p class="text-[10px] text-slate-400 italic">{msg.text}</p>
					</div>
				{/if}
			{/each}

			{#if thinking}
				<div class="flex justify-start">
					<div class="rounded-2xl rounded-tl-sm border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-400 animate-pulse">
						thinking…
					</div>
				</div>
			{/if}
		</div>

		<!-- Error bar -->
		{#if session.error}
			<div class="px-4 py-2 border-t bg-red-50 text-red-600 text-xs shrink-0">{session.error}</div>
		{/if}

		<!-- Input bar -->
		<div class="flex items-end gap-2 px-3 py-2.5 bg-slate-50 border-t shrink-0">
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<textarea
				bind:value={inputText}
				onkeydown={onKeydown}
				placeholder={connected ? 'Reply… (Enter to send, Shift+Enter for newline)' : 'Connecting…'}
				disabled={!connected || thinking}
				rows={2}
				class="flex-1 resize-none rounded-lg border border-slate-300 bg-white text-slate-900
				       placeholder:text-slate-400 px-3 py-2 text-sm focus:outline-none focus:ring-2
				       focus:ring-slate-400 disabled:opacity-50"
			></textarea>

			<div class="flex flex-col gap-1.5 shrink-0">
				<button
					onclick={send}
					disabled={!inputText.trim() || !connected || thinking}
					class="px-3 py-1.5 text-xs rounded font-medium transition-colors
					       {inputText.trim() && connected && !thinking
						       ? 'bg-slate-800 text-white hover:bg-slate-700'
						       : 'bg-slate-200 text-slate-400 cursor-not-allowed'}"
				>Send</button>

				<button
					onclick={interrupt}
					disabled={!thinking}
					class="px-3 py-1.5 text-xs rounded font-medium transition-colors
					       {thinking
						       ? 'bg-red-600 text-white hover:bg-red-500'
						       : 'bg-slate-200 text-slate-400 cursor-not-allowed'}"
				>Stop</button>
			</div>
		</div>

	</div>
{/if}
