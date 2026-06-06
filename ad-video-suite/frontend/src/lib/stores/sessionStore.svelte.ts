import type { ChatMsg, SessionEntry, SessionStatus } from '$lib/types';

export const sessionStore = $state({
	sessions: [] as SessionEntry[],
	activeKey: null as string | null,
});

function findIdx(key: string): number {
	return sessionStore.sessions.findIndex((s) => s.key === key);
}

export function launchSession(
	agentId: string,
	agentName: string,
	cwd: string,
	campaign: string,
	wsUrl: string
): void {
	const key = `${agentId}::${cwd}`;
	const existing = sessionStore.sessions.find((s) => s.key === key);
	if (existing) {
		sessionStore.activeKey = key;
		return;
	}
	sessionStore.sessions.push({
		key,
		agentId,
		agentName,
		cwd,
		campaign,
		wsUrl,
		status: 'idle',
		messages: [],
		sessionInfo: null,
		turnCount: 0,
		error: '',
	});
	sessionStore.activeKey = key;
}

export function setActiveSession(key: string): void {
	sessionStore.activeKey = key;
}

export function getSession(key: string): SessionEntry | undefined {
	return sessionStore.sessions.find((s) => s.key === key);
}

export function getSessionsForCwd(cwd: string): SessionEntry[] {
	return sessionStore.sessions.filter((s) => s.cwd === cwd);
}

export function pushMessage(key: string, msg: ChatMsg): void {
	const i = findIdx(key);
	if (i === -1) return;
	// Direct push to preserve object reference — spread-replace would risk re-mounting the panel
	sessionStore.sessions[i].messages.push(msg);
}

export function setStatus(key: string, status: SessionStatus): void {
	const i = findIdx(key);
	if (i !== -1) sessionStore.sessions[i].status = status;
}

export function setSessionInfo(
	key: string,
	info: { model: string; sessionId: string } | null
): void {
	const i = findIdx(key);
	if (i !== -1) sessionStore.sessions[i].sessionInfo = info;
}

export function incrementTurnCount(key: string): void {
	const i = findIdx(key);
	if (i !== -1) sessionStore.sessions[i].turnCount++;
}

export function setError(key: string, error: string): void {
	const i = findIdx(key);
	if (i !== -1) sessionStore.sessions[i].error = error;
}

export function removeSession(key: string): void {
	const i = findIdx(key);
	if (i === -1) return;
	sessionStore.sessions.splice(i, 1);
	if (sessionStore.activeKey === key) {
		sessionStore.activeKey =
			sessionStore.sessions[Math.max(0, i - 1)]?.key ?? null;
	}
}

export function closeAllSessions(): void {
	sessionStore.sessions = [];
	sessionStore.activeKey = null;
}
