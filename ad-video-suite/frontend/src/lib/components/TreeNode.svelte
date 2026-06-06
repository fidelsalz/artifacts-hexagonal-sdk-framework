<script lang="ts">
	import TreeNode from './TreeNode.svelte';

	type TreeNodeData = {
		name: string;
		path: string;
		available_agents: string[];
		children: TreeNodeData[];
	};

	let { node, depth = 0 }: { node: TreeNodeData; depth?: number } = $props();
</script>

<div style="padding-left: {depth * 1.25}rem">
	<div class="flex items-center gap-2 py-1.5">
		<span class="text-slate-400 text-xs select-none">{depth > 0 ? '└' : '📁'}</span>
		<span class="text-sm font-medium text-slate-800">{node.name}</span>
		{#each node.available_agents as agent}
			<span class="bg-slate-100 text-slate-700 text-xs font-semibold rounded-full px-2.5 py-0.5">
				{agent}
			</span>
		{/each}
	</div>
	{#each node.children as child}
		<TreeNode node={child} depth={depth + 1} />
	{/each}
</div>
