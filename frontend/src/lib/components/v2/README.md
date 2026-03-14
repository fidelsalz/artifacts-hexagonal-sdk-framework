# v2 Components

**Purpose:** Custom components for new hexagonal architecture features

## Guidelines

1. **Always use shadcn-svelte first** - Check `../ui/` for available components
2. **Create reusable components** - Never write inline UI code
3. **Use TypeScript** - Define props with types
4. **Follow naming** - Component names should be descriptive (e.g., `OrderCard.svelte`, `StoreSelector.svelte`)

## Structure

```
v2/
├── README.md (this file)
├── OrderCard.svelte
├── StoreSelector.svelte
├── InventoryAlertTable.svelte
└── [feature-specific-components].svelte
```

## Example Component

```svelte
<!-- StoreSelector.svelte -->
<script lang="ts">
  import { Select } from "$lib/components/ui/select";


  ];
</script>

<Select.Root bind:value={selectedStore} on:change={() => onStoreChange(selectedStore)}>
  <Select.Trigger>
    <Select.Value placeholder="Select store" />
  </Select.Trigger>
  <Select.Content>
    {#each stores as store}
      <Select.Item value={store.id}>{store.name}</Select.Item>
    {/each}
  </Select.Content>
</Select.Root>
```

## Component Checklist

Before creating a component:

- [ ] Check if shadcn-svelte has it: https://www.shadcn-svelte.com/docs/components
- [ ] Check if already exists in `../ui/`
- [ ] If not, add via: `npx shadcn-svelte@latest add [component-name]`
- [ ] Only create custom component if unavailable in shadcn


