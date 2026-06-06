<script lang="ts">
	import type { HTMLInputAttributes } from 'svelte/elements';

	let { class: className = '', value = $bindable(), ...rest }: HTMLInputAttributes = $props();
</script>

<input
	class="flex h-9 w-full rounded-md border border-slate-200 bg-white px-3 py-1 text-sm
	       placeholder:text-slate-400 shadow-xs transition-colors
	       focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-2
	       disabled:cursor-not-allowed disabled:opacity-50 {className}"
	bind:value
	{...rest}
/>
