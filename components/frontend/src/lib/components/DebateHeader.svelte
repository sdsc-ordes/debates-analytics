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

  .debate-form {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
</style>