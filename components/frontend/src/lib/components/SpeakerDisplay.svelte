<script lang="ts">
  import { auth } from "$lib/auth";
  import { client } from '$lib/api/client';
  import type { components } from '$lib/api/schema';
  import { User, Briefcase, MapPin, Pencil } from 'lucide-svelte';
  import Modal from '$lib/components/FormEditModal.svelte';

  type Speaker = components['schemas']['Speaker'];

  interface Props {
    speakers: Speaker[];
    activeSpeaker?: Speaker;
    mediaId: string;
  }

  let {
    speakers = $bindable(),
    activeSpeaker,
    mediaId
  }: Props = $props();

  let showModal = $state(false);
  let errorMessage = $state<string | null>(null);
  let isSaving = $state(false);

  const FIELDS = [
    { key: 'name', label: 'Name', placeholder: 'Enter name', icon: User },
    { key: 'role_tag', label: 'Role', placeholder: 'Enter role', icon: Briefcase },
    { key: 'country', label: 'Country', placeholder: 'Enter country', icon: MapPin }
  ] as const;

  let draftData = $state<Record<string, string>>({});
  let editingSpeakerId = $state<string | null>(null);

  // Watch for external changes (e.g. video playing forward)
  $effect(() => {
    if (showModal && activeSpeaker?.speaker_id !== editingSpeakerId) {
      closeModal();
    }
  });

  function openModal() {
    if (!activeSpeaker) return;

    FIELDS.forEach(field => {
      // @ts-ignore - Dynamic access to speaker properties
      draftData[field.key] = activeSpeaker[field.key] || '';
    });

    editingSpeakerId = activeSpeaker.speaker_id || null;
    errorMessage = null;
    showModal = true;
  }

  function closeModal() {
    showModal = false;
    errorMessage = null;
    editingSpeakerId = null;
    draftData = {};
  }

  async function saveSpeakers() {
    if (!activeSpeaker) return;

    isSaving = true;

    FIELDS.forEach(field => {
      // @ts-ignore - Dynamic assignment
      activeSpeaker[field.key] = draftData[field.key];
    });

    const SpeakerUpdateRequest = {
      media_id: mediaId,
      speakers: speakers,
    };

    try {
      const { error: speakerUpdateError } = await client.POST("/db/update-speakers", {
          body: SpeakerUpdateRequest,
      });

      if (speakerUpdateError) {
        throw new Error("Update of speakers failed.");
      }

      closeModal();
    } catch (err: any) {
      errorMessage = err.message || 'Unknown error occurred';
      console.error(err);
    } finally {
      isSaving = false;
    }
  }
</script>

<div class="speaker-card">
  {#if activeSpeaker}
    <div class="speaker-header">
      <span class="speaker-id">{activeSpeaker.speaker_id}</span>
      {#if auth.canEdit}
        <button class="edit-btn" onclick={openModal} title="Edit speaker">
          <Pencil size={14} />
        </button>
      {/if}
    </div>

    <div class="speaker-info">
      <div class="speaker-name">
        {activeSpeaker.name || 'Unknown Speaker'}
      </div>

      {#if activeSpeaker.role_tag}
        <div class="speaker-detail">
          <Briefcase size={14} />
          <span>{activeSpeaker.role_tag}</span>
        </div>
      {/if}

      {#if activeSpeaker.country}
        <div class="speaker-detail">
          <MapPin size={14} />
          <span>{activeSpeaker.country}</span>
        </div>
      {/if}

      {#if !activeSpeaker.name && !activeSpeaker.role_tag && !activeSpeaker.country}
        <p class="no-details">No details available</p>
      {/if}
    </div>

  {:else}
    <div class="no-speaker">
      <User size={24} strokeWidth={1.5} />
      <p>No active speaker</p>
    </div>
  {/if}
</div>

<Modal show={showModal} title="Edit Speaker" onClose={closeModal}>
  <div class="speaker-id-badge">{editingSpeakerId}</div>

  {#if errorMessage}
    <div class="error-message">{errorMessage}</div>
  {/if}

  <form class="speaker-form" onsubmit={(e) => { e.preventDefault(); saveSpeakers(); }}>
    {#each FIELDS as field}
      <div class="form-group">
        <label for="speaker-{field.key}" class="form-label">
          {#if field.key === 'name'}
            <User size={14} />
          {:else if field.key === 'role_tag'}
            <Briefcase size={14} />
          {:else}
            <MapPin size={14} />
          {/if}
          {field.label}
        </label>
        <input
          id="speaker-{field.key}"
          placeholder={field.placeholder}
          type="text"
          bind:value={draftData[field.key]}
          class="form-input"
        />
      </div>
    {/each}

    <button type="submit" style="display: none;" aria-hidden="true">Submit</button>
  </form>

  {#snippet footer()}
    <button class="form-btn form-btn-secondary" onclick={closeModal} type="button" disabled={isSaving}>
      Cancel
    </button>
    <button class="form-btn form-btn-primary" onclick={saveSpeakers} type="button" disabled={isSaving}>
      {isSaving ? 'Saving...' : 'Save Changes'}
    </button>
  {/snippet}
</Modal>

<style>
  .speaker-card {
    background: white;
    border: 1px solid #eaeaea;
    border-radius: 10px;
    padding: 1rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  }

  .speaker-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 0.75rem;
    margin-bottom: 0.75rem;
    border-bottom: 1px solid var(--bg-muted);
  }

  .speaker-id,
  .speaker-id-badge {
    font-size: 11px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    background: var(--bg-muted);
    padding: 4px 8px;
    border-radius: 4px;
  }

  .speaker-id-badge {
    font-size: 10px;
    padding: 3px 6px;
    display: inline-block;
    margin-bottom: 0.75rem;
  }

  .speaker-info {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .speaker-name {
    font-size: 18px;
    font-weight: 600;
    color: var(--text-color);
    margin-bottom: 0.25rem;
  }

  .speaker-detail {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: var(--text-muted);
  }

  .no-details,
  .no-speaker p {
    font-size: 13px;
    color: var(--text-light);
    margin: 0;
  }

  .no-details {
    font-style: italic;
  }

  .no-speaker {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem 1rem;
    color: var(--text-light);
    gap: 0.5rem;
  }

  .speaker-form {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
</style>
