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

  // --- CONFIGURATION ---
  const FIELDS = [
    { key: 'session', label: 'Session', type: 'text', placeholder: 'e.g. 55th Session' },
    { key: 'debate_type', label: 'Type', type: 'text', placeholder: 'e.g. Working Group' },
    // Note: type="date" inputs expect "YYYY-MM-DD"
    { key: 'date', label: 'Date', type: 'date', placeholder: '' }, 
    { key: 'link_mediasource', label: 'Link Mediasource', type: 'url', placeholder: 'https://...' },
    { key: 'link_agenda', label: 'Link Agenda', type: 'url', placeholder: 'https://...' },
  ] as const;

  // --- DRAFT STATE ---
  let draftData = $state<Record<string, string>>({});

  function startEdit() {
    FIELDS.forEach(field => {
        // @ts-ignore - dynamic access
        const val = debate[field.key];

        if (field.key === 'date' && val) {
            // For <input type="date">, we need YYYY-MM-DD (first 10 chars)
            draftData[field.key] = val.slice(0, 10);
        } else {
            draftData[field.key] = val || "";
        }
    });

    errorMessage = null;
    isEditing = true;
  }

  function cancelEdit() {
    isEditing = false;
    errorMessage = null;
    draftData = {};
  }

  async function saveDebate() {
    const oldDebate = $state.snapshot(debate);

    // 1. Optimistic Update
    FIELDS.forEach(field => {
        const val = draftData[field.key];
        // @ts-ignore
        debate[field.key] = val || null; // Save as null if empty string
    });

    isEditing = false;
    errorMessage = null;

    try {
      // 2. Send ALL fields to the backend
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

    } catch (err: any) {
      console.error(err);
      errorMessage = "Save failed. Reverting changes.";
      Object.assign(debate, oldDebate); // Revert UI
      isEditing = true;
    }
  }

  const get_debate_title = () => {
      // Fixed: use 'debate_type' to match schema
      const parts = [debate.session, debate.debate_type].filter(Boolean);
      return parts.length > 0 ? parts.join(' - ') : debate.media_id;
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
        {#each FIELDS as field}
            <label for="debate-{field.key}" class="input-label">{field.label}</label>
            <input
              id="debate-{field.key}"
              type={field.type}
              placeholder={field.placeholder}
              bind:value={draftData[field.key]}
              class="editable-input"
            />
        {/each}

        <button type="submit" style="display: none;"></button>
      </form>

      <div class="button-group">
        <button class="secondary-button" onclick={cancelEdit} type="button">Cancel</button>
        <button class="secondary-button" onclick={saveDebate} type="button">Save</button>
      </div>

    {:else}
      <div class="header-content">
        <div>
            <div class="card-title-large" style="color: var(--primary-dark-color);">
                {get_debate_title()}
            </div>

            <div class="metadata-grid" style="margin-top: 1rem;">
                {#each FIELDS as field}
                    {#if field.key !== 'session' && field.key !== 'debate_type'}
                        <div class="metadata-item">
                            <span class="input-label" style="margin-bottom: 0;">{field.label}:</span>

                            <span class="display-text">
                                {#if !debate[field.key]}
                                    <span style="opacity: 0.5;">-</span>
                                {:else if field.type === 'url'}
                                    <a href={debate[field.key]} target="_blank" rel="noopener noreferrer" class="link">
                                        Open Link ↗
                                    </a>
                                {:else if field.key === 'date'}
                                    {displayIsoDate(debate[field.key])}
                                {:else}
                                    {debate[field.key]}
                                {/if}
                            </span>
                        </div>
                    {/if}
                {/each}
            </div>
        </div>

        {#if $canEdit}
            <div class="button-group" style="align-self: flex-start;">
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
    /* Optional quick styling for the metadata grid */
    .metadata-grid {
        display: grid;
        grid-template-columns: auto 1fr;
        column-gap: 1rem;
        row-gap: 0.5rem;
        align-items: center;
    }
    .link {
        color: var(--primary-color);
        text-decoration: none;
    }
    .link:hover {
        text-decoration: underline;
    }

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