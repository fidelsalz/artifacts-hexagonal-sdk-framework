<script lang="ts">
  import './layout.css';
  import NavMenu from '$lib/components/v2/NavMenu.svelte';
  let { children } = $props();
</script>

<div class="min-h-screen bg-gray-50">
  <header class="bg-white border-b border-gray-200">
    <div class="container mx-auto px-4 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <a href="/" class="text-lg font-bold hover:text-primary transition-colors">
            SDK Agents Suite
          </a>
      </div>
        <NavMenu />
      </div>
    </div>
  </header>

  <main class="container mx-auto px-4 py-8">
    {@render children()}
  </main>
</div>
