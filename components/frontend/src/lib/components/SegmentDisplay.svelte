<script lang="ts">
  import { auth } from "$lib/auth";
  import { jumpToTime } from "$lib/utils/mediaStartUtils";
  import type { components } from '$lib/api/schema';
  import { client } from '$lib/api/client';
  import { Pencil, Check, X } from 'lucide-svelte';

  type Segment = components['schemas']['Segment'];

  // Define types locally if not exported from schema
  const typeTranscript = "original"
  const typeTranslation = "translation"

  interface Props {
    activeSegment?: Segment;
    mediaElement?: HTMLMediaElement;
    mediaId: string;
    currentTime: number,
    term: string,
  }

  let {
    activeSegment,
    mediaElement,
    mediaId,
    currentTime,
    term,
  }: Props = $props();

  let editTranscript = $state(false);
  let editTranslation = $state(false);
  let errorMessage = $state<string | null>(null);

  let activeGroupOriginal = $derived(activeSegment?.subtitles_original || []);
  let activeGroupTranslation = $derived(activeSegment?.subtitles_translation || []);

  // 2. Find the specific subtitle INSIDE that segment
  let currentSubtitle = $derived(
    activeSegment?.subtitles_original.find(s => currentTime >= s.start && currentTime <= s.end)
  );

  let currentSubtitleEn = $derived(
    activeSegment?.subtitles_translation.find(s => currentTime >= s.start && currentTime <= s.end)
  );

  function escapeRegExp(string: string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function getHighlightedParts(text: string, query: string) {
    if (!query) return [{ text, isMatch: false }];

    const escaped = escapeRegExp(query);
    const regex = new RegExp(`(${escaped})`, 'gi');

    return text.split(regex).map(part => ({
      text: part,
      isMatch: part.toLowerCase() === query.toLowerCase()
    })).filter(p => p.text);
  }

  // Store backups separately for original and translation
  let backups = $state<{ [key: string]: string[] }>({
    [typeTranscript]: [],
    [typeTranslation]: []
  });

  const toggleEditTranscript = (val: boolean) => {
    if (val) {
      // Take snapshot
      backups[typeTranscript] = activeGroupOriginal.map(item => item.text);
      editTranscript = true;
    } else {
      // Revert: Assign the strings back to the reactive array items
      activeGroupOriginal.forEach((item, i) => {
        item.text = backups[typeTranscript][i];
      });
      editTranscript = false;
    }
  };

  const toggleEditTranslation = (val: boolean) => {
    if (val) {
      backups[typeTranslation] = activeGroupTranslation.map(item => item.text);
      editTranslation = true;
    } else {
      activeGroupTranslation.forEach((item, i) => {
        item.text = backups[typeTranslation][i];
      });
      editTranslation = false;
    }
  };

  async function saveGroup(group: any[], type: string) {
    if (!activeSegment) return;
    errorMessage = null;

    try {
      const payload = {
        media_id: mediaId,
        segment_nr: activeSegment.segment_nr,
        subtitles: group,
        subtitle_type: type,
      };

      const { error: segmentUpdateError } = await client.POST("/db/update-subtitles", {
        body: payload,
      });

      if (segmentUpdateError) throw new Error(`Update failed: ${segmentUpdateError}`);

      // SUCCESS: Clear backup and close editor
      backups[type] = [];
      if (type === typeTranscript) editTranscript = false;
      if (type === typeTranslation) editTranslation = false;

    } catch (err: any) {
      errorMessage = err.message || 'Unknown error occurred';
    }
  }
</script>

{#snippet subtitleColumn(
  title: string,
  group: any[],
  isEditing: boolean,
  type: string,
  currentSub: any,
  setEditing: (v: boolean) => void
)}
  <div class="text-block">
    <div class="header-row">
      <div class="card-title-small">{title}</div>
      {#if auth.canEdit && activeSegment}
        {#if !isEditing}
          <button class="edit-btn" onclick={() => setEditing(true)} title="Edit {title}">
            <Pencil size={14} />
          </button>
        {:else}
          <div class="edit-actions">
            <button class="edit-btn cancel" onclick={() => setEditing(false)} title="Cancel">
              <X size={14} />
            </button>
            <button class="edit-btn save" onclick={() => saveGroup(group, type)} title="Save">
              <Check size={14} />
            </button>
          </div>
        {/if}
      {/if}
    </div>

    <p class="subtitle-content">
      {#each group as item}
        <span
          class="subtitle-span {item === currentSub ? 'highlighted' : ''}"
          onclick={() => mediaElement && jumpToTime(mediaElement, item.start)}
          role="button"
          tabindex="0"
          onkeydown={() => {}}
        >
          {#if isEditing}
            <textarea
              bind:value={item.text}
              class="editable-textarea"
              rows="2"
              onclick={(e) => e.stopPropagation()}
            ></textarea>
          {:else}
            {#each getHighlightedParts(item.text, term) as part}
              {#if part.isMatch}
                <mark class="term-highlight">{part.text}</mark>
              {:else}
                {part.text}
              {/if}
            {/each}
            {" "}
          {/if}
        </span>
      {/each}
    </p>
  </div>
{/snippet}

<div class="side-by-side">
  {#if activeGroupOriginal.length > 0}
    {@render subtitleColumn("Transcription", activeGroupOriginal, editTranscript, typeTranscript, currentSubtitle, toggleEditTranscript)}
  {/if}

  {#if activeGroupTranslation.length > 0}
    {@render subtitleColumn("Translation", activeGroupTranslation, editTranslation, typeTranslation, currentSubtitleEn, toggleEditTranslation)}
  {/if}
</div>

{#if errorMessage}
    <div class="alert alert-danger">{errorMessage}</div>
{/if}

<style>
  .side-by-side {
    display: flex;
    justify-content: space-between;
    gap: 2rem;
    max-height: 300px;
    padding: 0.5rem;
  }

  .text-block {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .text-block p {
    overflow-y: auto;
  }

  .header-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .highlighted {
    color: var(--secondary-color);
    font-weight: bold;
  }

  .editable-textarea {
    width: 100%;
    height: 50px;
  }

  p {
    margin: 0;
    padding: 0;
    word-wrap: break-word;
  }

  .term-found {
    background-color: #fff9c4;
    border-radius: 2px;
    box-shadow: 0 0 2px #fbc02d;
  }
  .term-highlight {
    background-color: #fff9c4; /* Yellow highlight */
    color: inherit;
    border-radius: 2px;
    padding: 0 1px;
    font-weight: bold; /* Optional: make the search term pop */
  }
</style>
