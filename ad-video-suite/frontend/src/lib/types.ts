export type AgentStatus = 'completed' | 'ready' | 'blocked';

export type TreeAgentRef = {
	id: string;
	status: AgentStatus;
	blocked_by: string[];
};

export type TreeNodeData = {
	name: string;
	path: string;
	available_agents: TreeAgentRef[];
	children: TreeNodeData[];
};

export type AgentCandidate = {
	id: string;
	name: string;
	role: string;
	status?: AgentStatus;
	blocked_by?: string[];
};

export type FileEntry = {
	name: string;
	type: 'dir' | 'file';
	path: string;
};

export type CampaignData = {
	slug: string;
	name: string;
	created_at: string;
	path: string;
	variations_generated: number;
};

export type ChatMsg = {
	role: 'user' | 'assistant' | 'status' | 'result';
	text?: string;
	duration_ms?: number;
	total_cost_usd?: number;
	num_turns?: number;
};

export type SessionStatus = 'idle' | 'connecting' | 'connected' | 'thinking' | 'error' | 'closed';

export type SessionEntry = {
	key: string; // `${agentId}::${cwd}`
	agentId: string;
	agentName: string;
	cwd: string;
	campaign: string;
	wsUrl: string; // relative path from /api/launch, e.g. /ws/agents/arcs/chat?cwd=...
	status: SessionStatus;
	messages: ChatMsg[];
	sessionInfo: { model: string; sessionId: string } | null;
	turnCount: number;
	error: string;
};
