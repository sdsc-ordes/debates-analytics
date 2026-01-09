<script lang="ts">
  import { canEdit } from "$lib/stores/auth";
  import { displayIsoDate } from "$lib/utils/displayUtils";
  import { client } from '$lib/api/client';
  import type { components } from '$lib/api/schema';

  type DebateDocument = components['schemas']['DebateDocument'];

  interface Props {
    debate: DebateDocument;
  }

  let { debate = $bindable() }: Props = $props();

  let isEditing = $state(false);
  let errorMessage = $state<string | null>(null);

  // --- DRAFT STATE ---
  let draftSession = $state("");
  let draftType = $state("");
  let draftSchedule = $state("");

  function startEdit() {
    // Copy current values to draft
    draftSession = debate.session || "";
    draftType = debate.type || "";

    // Format ISO date for datetime-local input (YYYY-MM-DDTHH:mm)
    // If debate.schedule is undefined, use empty string.
    draftSchedule = debate.schedule ? debate.schedule.slice(0, 16) : "";

    errorMessage = null;
    isEditing = true;
  }

  function cancelEdit() {
    isEditing = false;
    errorMessage = null;
  }

  async function saveDebate() {
    // 1. Optimistic Update (Update UI immediately)
    const oldDebate = { ...debate };
    
    debate.session = draftSession;
    debate.type = draftType;
    // Append ':00Z' to make it a valid simplified ISO string if needed, 
    // or just save what the input gives if your backend handles it.
    debate.schedule = draftSchedule ? new Date(draftSchedule).toISOString() : null;

    isEditing = false;
    errorMessage = null;

    try {
      const { error } = await client.POST("/db/update-debate", {
        body: {
          media_id: debate.media_id,
          session: debate.session,
          type: debate.type,
          schedule: debate.schedule
        }
      });

      if (error) throw new Error("Update of debate details failed.");

    } catch (err: any) {
      console.error(err);
      errorMessage = "Save failed. Reverting changes.";
      debate = oldDebate; // Revert UI
      isEditing = true;   // Re-open edit mode
    }
  }

  const get_debate_title = () => {
      if (debate.session && debate.type) {
          return `${debate.session} ${debate.type}`
      } else if (debate.session) {
          return debate.session
      } else {
          return debate.media_id
      }
  }
</script>

<div class="card">
  <div class="card-body">
    
    {#if isEditing}
      <p class="card-subtle">Edit debate details:</p>
      
      {#if errorMessage}
        <div class="alert alert-danger">{errorMessage}</div>
      {/if}

      <form class="debate-form" onsubmit={(e) => { e.preventDefault(); saveDebate(); }}>
        
        <label for="debate-session" class="input-label">Session</label>
        <input
          id="debate-session"
          placeholder="e.g. 55th Session"
          type="text"
          bind:value={draftSession}
          class="editable-input"
        />

        <label for="debate-type" class="input-label">Type</label>
        <input
          id="debate-type"
          placeholder="e.g. Working Group"
          type="text"
          bind:value={draftType}
          class="editable-input"
        />

        <label for="debate-schedule" class="input-label">Date & Time</label>
        <input
          id="debate-schedule"
          type="datetime-local"
          bind:value={draftSchedule}
          class="editable-input"
        />

        <button type="submit" style="display: none;"></button>
      </form>

      <div class="button-group">
        <button class="secondary-button" onclick={cancelEdit} type="button">
          Cancel
        </button>
        <button class="secondary-button" onclick={saveDebate} type="button">
          Save
        </button>
      </div>

    {:else}
      <div class="header-content">
        <div>
            <div class="card-title-large" style="color: var(--primary-dark-color);">
            {get_debate_title()}
            </div>

            {#if debate.schedule}
            <div class="date-time-item">
                <div class="card-title-small">{displayIsoDate(debate.schedule)}</div>
            </div>
            {/if}
        </div>

        {#if $canEdit}
            <div class="button-group">
                <button class="secondary-button" onclick={startEdit} aria-label="Edit">
                Edit
                </button>
            </div>
        {/if}
      </div>
    {/if}

  </div>
</div>

<style>
  /* Reuse the exact styles from your Speaker component */
  .card {
    max-width: 100%;
    border-radius: 10px;
    /* You can remove box-shadow/border if you want it to blend in more like a header */
    /* box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); */
    padding: 0.5rem 1rem;
    box-sizing: border-box;
    margin-bottom: 1rem; /* Add spacing below header */
  }

  .card-body {
    display: flex;
    flex-direction: column;
  }

  .debate-form {
    display: flex;
    flex-direction: column;
    gap: 0.5rem; 
  }

  .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
  }

  .input-label {
    font-size: 14px;
    font-weight: 500;
    color: #333;
    margin-top: 0.5rem;
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

  .button-group {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 0.25rem;
  }

  .card-subtle {
      font-size: 0.9rem;
      color: #666;
      margin-bottom: 1rem;
  }
</style>