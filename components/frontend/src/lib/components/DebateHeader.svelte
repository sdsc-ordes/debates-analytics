<script lang="ts">
  import { auth } from '$lib/auth';
  import { displayIsoDate } from "$lib/utils/displayUtils";
  import { client } from '$lib/api/client';
  import type { components } from '$lib/api/schema';
  import { Pencil, Calendar, Link, FileText, Briefcase } from 'lucide-svelte';
  import Modal from '$lib/components/FormEditModal.svelte';

  type DebateDocument = components['schemas']['DebateDocument'];

  interface Props {
    debate: DebateDocument;
  }

  let { debate = $bindable() }: Props = $props();

  let showModal = $state(false);
  let errorMessage = $state<string | null>(null);
  let isSaving = $state(false);

  const FIELDS = [
    { key: 'session', label: 'Session', type: 'text', placeholder: 'e.g. 55th Session', icon: Briefcase },
    { key: 'debate_type', label: 'Type', type: 'text', placeholder: 'e.g. Working Group', icon: FileText },
    { key: 'date', label: 'Date', type: 'date', placeholder: '', icon: Calendar },
    { key: 'link_mediasource', label: 'Media Source', type: 'url', placeholder: 'https://...', icon: Link },
    { key: 'link_agenda', label: 'Agenda', type: 'url', placeholder: 'https://...', icon: Link },
  ] as const;

  let draftData = $state<Record<string, string>>({});

  function openModal() {
    FIELDS.forEach(field => {
      // @ts-ignore - dynamic access
      const val = debate[field.key];

      if (field.key === 'date' && val) {
        draftData[field.key] = val.slice(0, 10);
      } else {
        draftData[field.key] = val || "";
      }
    });

    errorMessage = null;
    showModal = true;
  }

  function closeModal() {
    showModal = false;
    errorMessage = null;
    draftData = {};
  }

  async function saveDebate() {
    const oldDebate = $state.snapshot(debate);
    isSaving = true;

    FIELDS.forEach(field => {
      const val = draftData[field.key];
      // @ts-ignore
      debate[field.key] = val || null;
    });

    try {
      const { error } = await client.POST("/db/update-debate", {
        body: {
          media_id: debate.media_id,
          session: debate.session,
          debate_type: debate.debate_type,
          date: debate.date,
          link_agenda: debate.link_agenda,
          link_mediasource: debate.link_mediasource
        }
      });

      if (error) throw new Error("Update of debate details failed.");
      closeModal();
    } catch (err: any) {
      console.error(err);
      errorMessage = "Save failed. Please try again.";
      Object.assign(debate, oldDebate);
    } finally {
      isSaving = false;
    }
  }

  const getDebateTitle = () => {
    const parts = [debate.session, debate.debate_type].filter(Boolean);
    return parts.length > 0 ? parts.join(' - ') : 'Untitled Debate';
  }
</script>

{#if debate}
  <div class="debate-header">
    <h1 class="debate-title">{getDebateTitle()}</h1>

    <div class="metadata">
      {#if debate.date}
        <div class="metadata-item">
          <Calendar size={14} />
          <span>{displayIsoDate(debate.date)}</span>
        </div>
      {/if}

      {#if debate.link_mediasource}
        <a href={debate.link_mediasource} target="_blank" rel="noopener noreferrer" class="metadata-link">
          <Link size={14} />
          <span>Media Source</span>
        </a>
      {/if}

      {#if debate.link_agenda}
        <a href={debate.link_agenda} target="_blank" rel="noopener noreferrer" class="metadata-link">
          <Link size={14} />
          <span>Agenda</span>
        </a>
      {/if}

      {#if auth.canEdit}
        <button class="edit-btn" onclick={openModal} title="Edit debate details">
          <Pencil size={14} />
        </button>
      {/if}
    </div>
  </div>
{/if}

<Modal show={showModal} title="Edit Debate" onClose={closeModal} width="360px">
  {#if errorMessage}
    <div class="error-message">{errorMessage}</div>
  {/if}

  <form class="debate-form" onsubmit={(e) => { e.preventDefault(); saveDebate(); }}>
    {#each FIELDS as field}
      <div class="form-group">
        <label for="debate-{field.key}" class="form-label">
          {#if field.key === 'session'}
            <Briefcase size={14} />
          {:else if field.key === 'debate_type'}
            <FileText size={14} />
          {:else if field.key === 'date'}
            <Calendar size={14} />
          {:else}
            <Link size={14} />
          {/if}
          {field.label}
        </label>
        <input
          id="debate-{field.key}"
          type={field.type}
          placeholder={field.placeholder}
          bind:value={draftData[field.key]}
          class="form-input"
        />
      </div>
    {/each}

    <button type="submit" style="display: none;" aria-hidden="true">Submit</button>
  </form>

  {#snippet footer()}
    <button class="btn btn-secondary" onclick={closeModal} type="button" disabled={isSaving}>
      Cancel
    </button>
    <button class="btn btn-primary" onclick={saveDebate} type="button" disabled={isSaving}>
      {isSaving ? 'Saving...' : 'Save Changes'}
    </button>
  {/snippet}
</Modal>

<style>
  .debate-header {
    --border-color: #e2e8f0;
    --bg-muted: #f1f5f9;
    --text-muted: #64748b;
    --text-light: #94a3b8;

    padding-bottom: 1.25rem;
    margin-bottom: 1.25rem;
    border-bottom: 1px solid var(--border-color);
  }

  .debate-title {
    font-size: 22px;
    font-weight: 600;
    color: var(--primary-dark-color, var(--text-color));
    margin: 0 0 0.5rem 0;
  }

  .metadata {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    align-items: center;
  }

  .metadata-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: var(--text-muted);
  }

  .metadata-link {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: var(--primary-color);
    text-decoration: none;
    transition: opacity 0.2s;
  }

  .metadata-link:hover {
    opacity: 0.8;
  }

  .edit-btn {
    background: none;
    border: none;
    cursor: pointer;
    color: var(--text-light);
    padding: 4px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.2s, color 0.2s;
  }

  .edit-btn:hover {
    background: var(--bg-muted);
    color: var(--primary-color);
  }

  /* Form styles */
  .debate-form {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .form-label {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 12px;
    font-weight: 500;
    color: #475569;
  }

  .form-input {
    height: 36px;
    padding: 0 10px;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    font-size: 13px;
    width: 100%;
    box-sizing: border-box;
    transition: border-color 0.2s, box-shadow 0.2s;
  }

  .form-input:focus {
    border-color: var(--primary-color);
    outline: none;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  .form-input::placeholder {
    color: var(--text-light);
  }

  .error-message {
    background: #fef2f2;
    color: #b91c1c;
    padding: 10px 12px;
    border-radius: 6px;
    font-size: 13px;
    margin-bottom: 1rem;
  }

  /* Buttons */
  .btn {
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    border: none;
    cursor: pointer;
    transition: background-color 0.2s, opacity 0.2s;
  }

  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-secondary {
    background: white;
    color: #475569;
    border: 1px solid var(--border-color);
  }

  .btn-secondary:hover:not(:disabled) { background: #f8fafc; }

  .btn-primary {
    background: var(--primary-color);
    color: white;
  }

  .btn-primary:hover:not(:disabled) { opacity: 0.9; }
</style>