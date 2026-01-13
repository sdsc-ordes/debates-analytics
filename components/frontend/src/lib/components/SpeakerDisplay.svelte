<script lang="ts">
  import { auth } from "$lib/auth";
  import { client } from '$lib/api/client';
  import type { components } from '$lib/api/schema';

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

  let editSpeakers = $state(false);
  let errorMessage = $state<string | null>(null);

  const FIELDS = [
    { key: 'name', label: 'Name', placeholder: 'Enter name' },
    { key: 'role_tag', label: 'Role', placeholder: 'Enter role' },
    { key: 'country', label: 'Country', placeholder: 'Enter country' }
  ] as const;

  let draftData = $state<Record<string, string>>({});
  let editingSpeakerId = $state<string | null>(null);

  // Watch for external changes (e.g. video playing forward)
  $effect(() => {
    if (editSpeakers && activeSpeaker?.speaker_id !== editingSpeakerId) {
        cancelEdit();
    }
  });

  function startEdit() {
    if (!activeSpeaker) return;

    FIELDS.forEach(field => {
      // @ts-ignore - Dynamic access to speaker properties
      draftData[field.key] = activeSpeaker[field.key] || '';
    });

    editingSpeakerId = activeSpeaker.speaker_id || null;
    errorMessage = null;
    editSpeakers = true;
  }

  function cancelEdit() {
    editSpeakers = false;
    errorMessage = null;
    editingSpeakerId = null;
    draftData = {};
  }

  async function saveSpeakers() {
    if (!activeSpeaker) return;

    FIELDS.forEach(field => {
      // @ts-ignore - Dynamic assignment
      activeSpeaker[field.key] = draftData[field.key];
    });

    const SpeakerUpdateRequest = {
      media_id: mediaId,
      speakers: speakers,
    };

    editSpeakers = false;
    errorMessage = null;

    try {
      const { error: speakerUpdateError } = await client.POST("/db/update-speakers", {
          body: SpeakerUpdateRequest,
      });

      if (speakerUpdateError) {
        throw new Error("Update of speakers failed.");
      }
    } catch (err: any) {
      editSpeakers = true;
      errorMessage = err.message || 'Unknown error occurred';
      console.error(err);
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

      {#if auth.canEdit && editSpeakers}
        <p class="card-subtle">Edit speaker details below:</p>
        <form class="speaker-form" onsubmit={(e) => { e.preventDefault(); saveSpeakers(); }}>

          {#each FIELDS as field}
            <label for="speaker-{field.key}" class="input-label">{field.label}</label>
            <input
              id="speaker-{field.key}"
              placeholder={field.placeholder}
              type="text"
              bind:value={draftData[field.key]}
              class="editable-input"
            />
          {/each}

          <button type="submit" style="display: none;"></button>
        </form>

        <div class="button-group">
          <button class="secondary-button" onclick={cancelEdit} type="button">Cancel</button>
          <button class="secondary-button" onclick={saveSpeakers} type="button">Save</button>
        </div>

      {:else}
        <div class="speaker-display">
          {#each FIELDS as field}
            <label class="input-label">{field.label}</label>
            <div class="display-text">
              {activeSpeaker[field.key] || `${field.label} not provided`}
            </div>
          {/each}
        </div>

        {#if auth.canEdit}
          <div class="button-group">
            <button class="secondary-button" onclick={startEdit} aria-label="Edit">
              Edit
            </button>
          </div>
        {/if}
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
