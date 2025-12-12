<script lang="ts">
  import { canEdit } from "$lib/stores/auth";
  import type { components } from '$lib/api/schema';

  type Speaker = components['schemas']['Speaker'];

  interface Props {
    speakers: Speaker[];
    activeSpeaker?: Speaker; // activeSpeaker can be undefined!
    mediaId: string;
  }

  let {
    speakers = $bindable(),
    activeSpeaker,
    mediaId
  }: Props = $props();

  let editSpeakers = $state(false);
  let errorMessage = $state<string | null>(null);

  // --- DRAFT STATE ---
  // Hold changes here so we don't mutate the live object until we save.
  let draftName = $state('');
  let draftRole = $state('');
  let editingSpeakerId = $state<string | null>(null);

  // Watch for external changes (e.g. video playing forward)
  $effect(() => {
    // If the active speaker changes while we are editing, we must abort
    // to prevent overwriting the wrong person.
    if (editSpeakers && activeSpeaker?.speaker_id !== editingSpeakerId) {
        cancelEdit();
    }
  });

  function startEdit() {
    if (!activeSpeaker) return;
    
    // Copy current values to draft
    draftName = activeSpeaker.name || '';
    draftRole = activeSpeaker.role_tag || '';
    editingSpeakerId = activeSpeaker.speaker_id || null;
    
    errorMessage = null;
    editSpeakers = true;
  }

  function cancelEdit() {
    editSpeakers = false;
    errorMessage = null;
    editingSpeakerId = null;
  }

  async function saveSpeakers() {
    // 1. Safety Check: Ensure we still have a speaker to update
    if (!activeSpeaker) return;

    // 2. Commit Draft to Real State (Optimistic Update)
    // Because activeSpeaker is a reference to an object inside 'speakers',
    // updating it here updates the main array automatically.
    activeSpeaker.name = draftName;
    activeSpeaker.role_tag = draftRole;

    const SpeakerUpdateRequest = {
      media_id: mediaId,
      speakers: speakers,
    };

    editSpeakers = false;
    errorMessage = null;

    try {
      const response = await fetch('/api/speakers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(SpeakerUpdateRequest)
      });

      if (!response.ok) {
        const errorData = await response.json();
        errorMessage = errorData.error || `Save failed: ${response.status}`;
        console.error(errorMessage);
        editSpeakers = true; // Re-open on failure so user doesn't lose text
      }
    } catch (error: any) {
      errorMessage = `An unexpected error occurred: ${error.message}`;
      console.error(errorMessage);
      editSpeakers = true;
    }
  }
</script>

<div class="card">
  <div class="card-body">
    {#if activeSpeaker}
      <div class="card-title-small">{activeSpeaker.speaker_id}</div>

      {#if errorMessage}
        <div class="alert alert-danger">{errorMessage}</div>
      {/if}

      {#if $canEdit}
        {#if editSpeakers}
          <p class="card-subtle">Edit speaker details below:</p>
          <form class="speaker-form" onsubmit={(e) => { e.preventDefault(); saveSpeakers(); }}>
            
            <label for="speaker-name" class="input-label">Name</label>
            <input
              id="speaker-name"
              placeholder="Enter name"
              type="text"
              bind:value={draftName}
              class="editable-input"
            />

            <label for="speaker-role" class="input-label">Role</label>
            <input
              id="speaker-role"
              placeholder="Enter role"
              type="text"
              bind:value={draftRole}
              class="editable-input"
            />
            
            <button type="submit" style="display: none;"></button>
          </form>
          
          <div class="button-group">
            <button class="secondary-button" onclick={cancelEdit} type="button">
              Cancel
            </button>
            <button class="secondary-button" onclick={saveSpeakers} type="button">
              Save
            </button>
          </div>

        {:else}
          <div class="speaker-display">
            <label class="input-label">Name</label>
            <div class="display-text">{activeSpeaker.name || "Name not provided"}</div>

            <label class="input-label">Role</label>
            <div class="display-text">{activeSpeaker.role_tag || "Role not provided"}</div>
          </div>

          <div class="button-group">
            <button class="secondary-button" onclick={startEdit} aria-label="Edit">
              Edit
            </button>
          </div>
        {/if}

      {:else}
        <div class="speaker-display">
          <label class="input-label">Name</label>
          <div class="display-text">{activeSpeaker.name || "Name not provided"}</div>

          <label class="input-label">Role</label>
          <div class="display-text">{activeSpeaker.role_tag || "Role not provided"}</div>
        </div>
      {/if}

    {:else}
      <p class="card-subtle">No active speaker for this segment.</p>
    {/if}
  </div>
</div>

<style>
  .card {
    /* width: fit-content; */
    max-width: 100%;
    max-height: 100%;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    padding: 1rem;
    box-sizing: border-box;
  }

  .card-body {
    display: flex;
    flex-direction: column;
    /* gap: 1rem; */
  }

  .speaker-form,
  .speaker-display {
    display: flex;
    flex-direction: column;
    /* gap: 1rem; */
  }

  .input-label {
    font-size: 14px;
    font-weight: 500;
    color: #333;
  }

  .editable-input {
    height: 40px;
    padding: 0 10px;
    border: 1px solid #ccc;
    border-radius: 5px;
    font-size: 14px;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
    width: 100%;
  }

  .editable-input:focus {
    border-color: var(--primary-color);
    outline: none;
  }

  .editable-input::placeholder {
    color: gray;
    font-style: italic;
  }
  .display-text {
    height: 40px;
    padding: 0 10px;
    border: 1px solid #ccc;
    border-radius: 5px;
    font-size: 14px;
    color: grey;
    display: flex;
    align-items: center;
  }

  .button-group {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 1rem;
  }

</style>
