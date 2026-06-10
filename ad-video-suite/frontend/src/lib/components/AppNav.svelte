<script lang="ts">
	import { page } from '$app/state';
	import { NavigationMenu, Separator } from 'bits-ui';
	import type { Snippet } from 'svelte';

	let { right }: { right?: Snippet } = $props();

	const links = [
		{ href: '/', label: 'Campaigns' },
		{ href: '/dashboard', label: 'Dashboard' },
		{ href: '/timeline', label: 'Timeline' },
		{ href: '/settings', label: 'Settings' },
	];

	function isActive(href: string): boolean {
		if (href === '/') return page.url.pathname === '/';
		return page.url.pathname.startsWith(href);
	}
</script>

<header class="bg-white">
	<div class="px-8 h-14 flex items-center gap-6">
		<!-- Brand -->
		<span class="text-sm font-semibold text-slate-900 shrink-0">Ad Video Suite</span>

		<!-- Nav links -->
		<NavigationMenu.Root>
			<NavigationMenu.List class="flex items-center gap-0.5">
				{#each links as link}
					<NavigationMenu.Item>
						<NavigationMenu.Link
							href={link.href}
							active={isActive(link.href)}
							class="block px-3 py-1.5 rounded-md text-sm transition-colors
							       {isActive(link.href)
								       ? 'bg-slate-100 text-slate-900 font-medium'
								       : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'}"
						>
							{link.label}
						</NavigationMenu.Link>
					</NavigationMenu.Item>
				{/each}
			</NavigationMenu.List>
		</NavigationMenu.Root>

		<!-- Right-side slot -->
		{#if right}
			<div class="ml-auto">
				{@render right()}
			</div>
		{:else}
			<div class="flex-1"></div>
		{/if}
	</div>
	<Separator.Root class="h-px bg-slate-200/60" />
</header>
