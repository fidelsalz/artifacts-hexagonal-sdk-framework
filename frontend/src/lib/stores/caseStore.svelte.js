import { API_BASE_URL } from '$lib/config.js';

// ---------------------------------------------------------------------------
// Pairing: coding agent → validator
// ---------------------------------------------------------------------------

const VALIDATOR_PAIR = {
  'ports':    'ports-validator',
  'adapters': 'adapters-validator',
  'hexagon':  'hexagon-validator',
  'infra':    'infra-validator',
};

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

export const caseState = $state({
  name: 'case-001',
  caseId: '#1032',
  status: 'idle',       // idle | active | complete | error
  totalCostUsd: 0,
  createdAt: null,

  agents: [
    { id: 'human-assistant',    label: 'Human Assistant',    commType: 'ws',  status: 'idle', lastRunAt: /** @type {string|null} */ (null), messages: /** @type {Record<string, any>[]} */ ([]), changedPaths: new Set() },
    { id: 'contracts-writer',   label: 'Contracts Writer',   commType: 'ws',  status: 'idle', lastRunAt: /** @type {string|null} */ (null), messages: /** @type {Record<string, any>[]} */ ([]), changedPaths: new Set() },
    { id: 'ports',              label: 'Ports Agent',        commType: 'sse', status: 'idle', lastRunAt: /** @type {string|null} */ (null), messages: /** @type {Record<string, any>[]} */ ([]), changedPaths: new Set() },
    { id: 'ports-validator',    label: 'Ports Validator',    commType: 'sse', status: 'idle', lastRunAt: /** @type {string|null} */ (null), messages: /** @type {Record<string, any>[]} */ ([]), mode: 'auto',   changedPaths: new Set() },
    { id: 'adapters',           label: 'Adapters Agent',     commType: 'sse', status: 'idle', lastRunAt: /** @type {string|null} */ (null), messages: /** @type {Record<string, any>[]} */ ([]), changedPaths: new Set() },
    { id: 'adapters-validator', label: 'Adapters Validator', commType: 'sse', status: 'idle', lastRunAt: /** @type {string|null} */ (null), messages: /** @type {Record<string, any>[]} */ ([]), mode: 'manual', changedPaths: new Set() },
    { id: 'hexagon',            label: 'Hexagon Agent',      commType: 'sse', status: 'idle', lastRunAt: /** @type {string|null} */ (null), messages: /** @type {Record<string, any>[]} */ ([]), changedPaths: new Set() },
    { id: 'hexagon-validator',  label: 'Hexagon Validator',  commType: 'sse', status: 'idle', lastRunAt: /** @type {string|null} */ (null), messages: /** @type {Record<string, any>[]} */ ([]), mode: 'auto',   changedPaths: new Set() },
    { id: 'infra',              label: 'Infra Agent',        commType: 'sse', status: 'idle', lastRunAt: /** @type {string|null} */ (null), messages: /** @type {Record<string, any>[]} */ ([]), changedPaths: new Set() },
    { id: 'infra-validator',    label: 'Infra Validator',    commType: 'sse', status: 'idle', lastRunAt: /** @type {string|null} */ (null), messages: /** @type {Record<string, any>[]} */ ([]), mode: 'manual', changedPaths: new Set() },
  ],
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** @param {string} id */
export function getAgent(id) {
  return caseState.agents.find((a) => a.id === id);
}

// ---------------------------------------------------------------------------
// SSE runner
// ---------------------------------------------------------------------------

/** @type {Map<string, EventSource>} */
const _connections = new Map();

/** Open an SSE stream for agentId and push events into caseState.
 * @param {string} agentId
 */
export function runAgent(agentId) {
  const agent = getAgent(agentId);
  if (!agent || agent.status === 'running') return;

  // Close any existing connection for this agent
  _connections.get(agentId)?.close();

  const now = new Date().toISOString();
  agent.status = 'running';
  agent.lastRunAt = now;
  // Always prepend a run-start marker (with timestamp) so every run is stamped
  agent.messages = [...agent.messages, { type: 'run-start', timestamp: now }];

  const evtSource = new EventSource(`${API_BASE_URL}/api/agents/${agentId}/stream`);
  _connections.set(agentId, evtSource);

  evtSource.onmessage = (event) => {
    const data = JSON.parse(event.data);

    // Route to the correct agent — validator events carry their own agent id
    const target = (data.agent && data.agent !== agentId)
      ? (getAgent(data.agent) ?? agent)
      : agent;

    // Mark validator as running on its first event
    if (data.agent && data.agent !== agentId && target.status !== 'running') {
      target.status = 'running';
    }

    if (data.type === 'done') {
      agent.status = 'done';
      evtSource.close();
      _connections.delete(agentId);
      // Auto-chain validator if mode is 'auto'
      const validatorId = /** @type {string | undefined} */ (/** @type {any} */ (VALIDATOR_PAIR)[agentId]);
      if (validatorId) {
        const validator = getAgent(validatorId);
        if (validator?.mode === 'auto') runAgent(validatorId);
      }

    } else if (data.type === 'error') {
      target.status = 'error';
      target.messages = [...target.messages, { type: 'status', text: data.message }];
      evtSource.close();
      _connections.delete(agentId);

    } else if (data.type === 'system') {
      target.messages = [...target.messages, {
        type: 'system',
        model: data.model,
        session_id: data.session_id,
        cwd: data.cwd,
        permission_mode: data.permission_mode,
        tools_count: data.tools_count,
      }];

    } else if (data.type === 'status') {
      target.messages = [...target.messages, { type: 'status', text: data.message }];

    } else if (data.type === 'assistant') {
      target.messages = [...target.messages, { type: 'assistant', text: data.text }];

    } else if (data.type === 'result') {
      const cost = data.total_cost_usd ?? 0;
      caseState.totalCostUsd += cost;
      target.status = 'done';
      target.messages = [...target.messages, {
        type: 'result',
        duration_ms: data.duration_ms,
        num_turns: data.num_turns,
        total_cost_usd: cost,
        input_tokens: data.input_tokens,
        output_tokens: data.output_tokens,
        cache_read_tokens: data.cache_read_tokens,
      }];
    }
  };

  evtSource.onerror = () => {
    if (agent.status === 'running') {
      agent.status = 'error';
      agent.messages = [...agent.messages, { type: 'status', text: 'Connection lost.' }];
    }
    evtSource.close();
    _connections.delete(agentId);
  };
}

/** Stop a running agent.
 * @param {string} agentId
 */
export function stopAgent(agentId) {
  _connections.get(agentId)?.close();
  _connections.delete(agentId);
  const agent = getAgent(agentId);
  if (agent && agent.status === 'running') agent.status = 'idle';
}

/** Toggle a validator between auto and manual mode.
 * @param {string} validatorId
 */
export function toggleValidatorMode(validatorId) {
  const agent = getAgent(validatorId);
  if (agent && 'mode' in agent) {
    /** @type {any} */ (agent).mode = agent.mode === 'auto' ? 'manual' : 'auto';
  }
}

/** Push a conversation message into a ws agent's history (persists across tab switches).
 * @param {string} agentId
 * @param {Record<string, any>} msg
 */
export function pushConvMessage(agentId, msg) {
  const agent = getAgent(agentId);
  if (agent) agent.messages = [...agent.messages, msg];
}

/** Set agent status.
 * @param {string} agentId
 * @param {string} status
 */
export function setAgentStatus(agentId, status) {
  const agent = getAgent(agentId);
  if (agent) agent.status = status;
}

/** Mark a file as changed for an agent (called by future file-change watcher).
 * @param {string} agentId
 * @param {string} filePath
 */
export function markFileChanged(agentId, filePath) {
  const agent = getAgent(agentId);
  if (agent) agent.changedPaths = new Set([...agent.changedPaths, filePath]);
}

/** Clear all changed-file markers for an agent.
 * @param {string} agentId
 */
export function clearFileChanges(agentId) {
  const agent = getAgent(agentId);
  if (agent) agent.changedPaths = new Set();
}
