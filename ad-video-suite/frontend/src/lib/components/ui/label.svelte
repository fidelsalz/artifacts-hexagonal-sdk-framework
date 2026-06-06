<script lang="ts">
	import { Label } from 'bits-ui';
	import type { Snippet } from 'svelte';

	let {
		class: className = '',
		children,
		...rest
	}: { class?: string; for?: string; children?: Snippet } = $props();
</script>

<Label.Root
	class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 {className}"
	{...rest}
>
	{@render children?.()}
</Label.Root>
