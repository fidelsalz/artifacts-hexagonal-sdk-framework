<script lang="ts">
  import { page } from '$app/stores';
  import * as NavigationMenu from '$lib/components/ui/navigation-menu';

  type MenuItem = { label: string; href: string; description: string; disabled?: boolean };

  const orders: MenuItem[] = [
    {
      label: 'Home',
      href: '/home',
      description: 'Back to home',
    },
    {
      label: 'Page 1',
      href: 'page1',
      description: 'Go to Page 1',
    },
  ];

  const tools: MenuItem[] = [
    {
      label: 'Dashboard',
      href: '/dashboard',
      description: 'Agents control panel',
    },
    {
      label: 'Agents',
      href: '/agents',
      description: 'Tabbed agent interaction screen',
    },
    {
      label: 'Task Logs Demo',
      href: 'task-logs-demo',
      description: 'Connect SSE',
    },
    {
      label: 'Basic Connection',
      href: '/basic-connect',
      description: 'SSE basic test',
    },
    {
      label: 'Agent Runner',
      href: '/agent-runner',
      description: 'Run SDK agent and stream output',
    },
  ];
</script>

<NavigationMenu.Root>
  <NavigationMenu.List>

    <!-- Orders -->
    <NavigationMenu.Item>
      <NavigationMenu.Trigger>Pages</NavigationMenu.Trigger>
      <NavigationMenu.Content>
        <ul class="grid w-[300px] gap-1 p-2">
          {#each orders as item}
            <li>
              <NavigationMenu.Link
                href={item.href}
                active={$page.url.pathname === item.href}
              >
                <span class="font-medium leading-none">{item.label}</span>
                <span class="text-xs text-muted-foreground leading-snug">{item.description}</span>
              </NavigationMenu.Link>
            </li>
          {/each}
        </ul>
      </NavigationMenu.Content>
    </NavigationMenu.Item>

    <!-- Tools -->
    <NavigationMenu.Item>
      <NavigationMenu.Trigger>Tools</NavigationMenu.Trigger>
      <NavigationMenu.Content>
        <ul class="grid w-[280px] gap-1 p-2">
          {#each tools as item}
            <li>
              <NavigationMenu.Link
                href={item.href}
                active={$page.url.pathname === item.href}
                class={item.disabled ? 'pointer-events-none opacity-50' : ''}
              >
                <div class="flex items-center justify-between">
                  <span class="font-medium leading-none">{item.label}</span>
                  {#if item.disabled}
                    <span class="text-[10px] uppercase tracking-wide text-muted-foreground border rounded px-1 py-0.5">Soon</span>
                  {/if}
                </div>
                <span class="text-xs text-muted-foreground leading-snug">{item.description}</span>
              </NavigationMenu.Link>
            </li>
          {/each}
        </ul>
      </NavigationMenu.Content>
    </NavigationMenu.Item>

  </NavigationMenu.List>
</NavigationMenu.Root>
