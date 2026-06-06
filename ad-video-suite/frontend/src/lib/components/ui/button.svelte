<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLButtonAttributes } from 'svelte/elements';

	type Variant = 'default' | 'outline' | 'ghost' | 'destructive';
	type Size = 'default' | 'sm';

	let {
		variant = 'default' as Variant,
		size = 'default' as Size,
		class: className = '',
		children,
		...rest
	}: HTMLButtonAttributes & { variant?: Variant; size?: Size; children?: Snippet } = $props();

	const base =
		'inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50';

	const variants: Record<Variant, string> = {
		default: 'bg-slate-900 text-slate-50 hover:bg-slate-700',
		outline: 'border border-slate-200 bg-white text-slate-900 hover:bg-slate-100',
		ghost: 'text-slate-900 hover:bg-slate-100',
		destructive: 'bg-red-600 text-white hover:bg-red-500',
	};

	const sizes: Record<Size, string> = {
		default: 'h-9 px-4 py-2',
		sm: 'h-8 px-3 text-xs',
	};
</script>

<button class="{base} {variants[variant]} {sizes[size]} {className}" {...rest}>
	{@render children?.()}
</button>
