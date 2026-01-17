<script lang="ts">
  import { X } from 'lucide-svelte';
  import type { Snippet } from 'svelte';

  interface Props {
    show: boolean;
    title: string;
    width?: string;
    onClose: () => void;
    children: Snippet;
    footer?: Snippet;
  }

  let { show, title, width = '320px', onClose, children, footer }: Props = $props();

  function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) {
      onClose();
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      onClose();
    }
  }
</script>

{#if show}
  <div
    class="modal-backdrop"
    onclick={handleBackdropClick}
    onkeydown={handleKeydown}
    role="dialog"
    aria-modal="true"
    aria-labelledby="modal-title"
    tabindex="-1"
  >
    <div class="modal" style="width: {width};">
      <div class="modal-header">
        <h3 id="modal-title">{title}</h3>
        <button class="close-btn" onclick={onClose} type="button" aria-label="Close">
          <X size={20} />
        </button>
      </div>

      <div class="modal-body">
        {@render children()}
      </div>

      {#if footer}
        <div class="modal-footer">
          {@render footer()}
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    z-index: 1000;
  }

  .modal {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: white;
    border-radius: 10px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
    display: flex;
    flex-direction: column;
    height: fit-content;
    z-index: 1001;
  }

  .modal-header,
  .modal-footer {
    display: flex;
    align-items: center;
    padding: 0.75rem 1rem;
  }

  .modal-header {
    justify-content: space-between;
    border-bottom: 1px solid var(--border-color);
  }

  .modal-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--text-color);
  }

  .close-btn {
    background: none;
    border: none;
    cursor: pointer;
    color: var(--text-light);
    padding: 4px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.2s, color 0.2s;
  }

  .close-btn:hover {
    background: var(--bg-muted);
    color: var(--text-muted);
  }

  .modal-body {
    padding: 1rem;
    overflow-y: auto;
  }

  .modal-footer {
    justify-content: flex-end;
    gap: 8px;
    border-top: 1px solid var(--border-color);
    background: #f8fafc;
  }
</style>
