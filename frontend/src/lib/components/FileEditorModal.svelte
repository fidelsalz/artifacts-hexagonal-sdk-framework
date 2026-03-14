<script lang="ts">
  import { API_BASE_URL } from '$lib/config.js';
  import { Dialog as DialogPrimitive } from 'bits-ui';
  import * as Dialog from '$lib/components/ui/dialog/index.js';

  type FileData = { path: string; content: string };

  let {
    file,
    onclose,
    onsaved,
  }: {
    file: FileData | null;
    onclose: () => void;
    onsaved?: (path: string) => void;
  } = $props();

  let editContent = $state('');
  let dirty       = $state(false);
  let saving      = $state(false);
  let error       = $state('');

  // Sync editor content whenever a new file is opened
  $effect(() => {
    if (file) {
      editContent = file.content;
      dirty = false;
      error = '';
    }
  });

  const filename = $derived(file ? file.path.split('/').at(-1) ?? file.path : '');

  function handleInput(e: Event) {
    editContent = (e.target as HTMLTextAreaElement).value;
    dirty = editContent !== file!.content;
  }

  async function save() {
    if (!file || !dirty || saving) return;
    saving = true;
    error = '';
    try {
      const r = await fetch(`${API_BASE_URL}/api/files/write`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: file.path, content: editContent }),
      });
      if (!r.ok) {
        const j = await r.json().catch(() => ({}));
        throw new Error(j.detail ?? r.statusText);
      }
      dirty = false;
      onsaved?.(file.path);
    } catch (e: any) {
      error = e.message ?? 'Save failed';
    } finally {
      saving = false;
    }
  }

  function discard() {
    if (file) { editContent = file.content; dirty = false; error = ''; }
  }

  function tryClose() {
    if (dirty && !confirm('Discard unsaved changes?')) return;
    onclose();
  }

  function onkeydown(e: KeyboardEvent) {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault();
      save();
    }
    if (e.key === 'Escape' && !dirty) {
      // Let Dialog handle Escape naturally when clean
    }
  }
</script>

<Dialog.Root
  open={file !== null}
  onOpenChange={(open) => { if (!open) tryClose(); }}
>
  <Dialog.Portal>
    <Dialog.Overlay />
    <DialogPrimitive.Content
      data-slot="dialog-content"
      class="bg-background data-[state=open]:animate-in data-[state=closed]:animate-out
             data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0
             data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95
             fixed top-1/2 left-1/2 z-50 -translate-x-1/2 -translate-y-1/2
             flex flex-col gap-0 p-0 rounded-lg border shadow-lg duration-200
             w-[80vw] max-w-[min(80vw,1100px)] max-h-[80vh]"
    >
    <!-- Title bar — dark background -->
    <div class="flex items-center gap-3 px-4 py-3 bg-zinc-900 rounded-t-lg">
      <div class="flex-1 min-w-0">
        <Dialog.Title class="text-sm font-semibold font-mono text-zinc-100 truncate">{filename}</Dialog.Title>
        <p class="text-[10px] text-zinc-400 font-mono truncate mt-0.5">{file?.path ?? ''}</p>
      </div>

      <!-- Status / dirty indicator -->
      {#if dirty}
        <span class="text-[10px] text-amber-400 font-medium shrink-0">● unsaved</span>
      {/if}

      <!-- Actions -->
      <div class="flex items-center gap-1.5 shrink-0">
        <button
          onclick={save}
          disabled={!dirty || saving}
          class="px-3 py-1 text-xs rounded font-medium transition-colors
                 {dirty && !saving
                   ? 'bg-zinc-100 text-zinc-900 hover:bg-white'
                   : 'bg-zinc-700 text-zinc-500 cursor-not-allowed'}"
        >{saving ? 'Saving…' : 'Save'}</button>

        <button
          onclick={discard}
          disabled={!dirty}
          class="px-3 py-1 text-xs rounded font-medium transition-colors
                 {dirty
                   ? 'bg-zinc-700 text-zinc-200 hover:bg-zinc-600'
                   : 'bg-zinc-700 text-zinc-500 cursor-not-allowed'}"
        >Discard</button>

        <button
          onclick={tryClose}
          class="px-2 py-1 rounded text-xs font-bold text-zinc-400 hover:bg-zinc-700 hover:text-zinc-100 transition-colors"
          title="Close (Escape)"
          aria-label="Close"
        >✕</button>
      </div>
    </div>

    <!-- Editor -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div class="flex-1 overflow-hidden" onkeydown={onkeydown}>
      <textarea
        value={editContent}
        oninput={handleInput}
        class="w-full h-full min-h-[50vh] resize-none p-4 font-mono text-[12px] leading-5
               bg-zinc-100 focus:outline-none"
        spellcheck="false"
        autocorrect="off"
        autocapitalize="off"
      ></textarea>
    </div>

    <!-- Footer: error + hint -->
    {#if error}
      <div class="px-4 py-2 bg-zinc-900 rounded-b-lg text-red-400 text-xs font-mono">{error}</div>
    {:else}
      <div class="px-4 py-1.5 bg-zinc-900 rounded-b-lg text-[10px] text-zinc-500">
        <kbd class="font-mono text-zinc-400">Ctrl+S</kbd> to save
      </div>
    {/if}
    </DialogPrimitive.Content>
  </Dialog.Portal>
</Dialog.Root>
