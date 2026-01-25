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

  async function saveGroup(group: Segment[], type: string) {
    if (!activeSegment) return;

    const payload = {
      media_id: mediaId,
      segment_nr: activeSegment.segment_nr,
      subtitles: group,
      subtitle_type: type,
    };

    errorMessage = null;

    try {
      const { error: segmentUpdateError } = await client.POST("/db/update-subtitles", {
          body: payload,
      });

      if (segmentUpdateError) {
        throw new Error(`Update of segment for ${type} failed.`);
      }
    } catch (err: any) {
      errorMessage = err.message || 'Unknown error occurred';
      console.error(err);
    }

    if (type === typeTranscript) editTranscript = false;
    if (type === typeTranslation) editTranslation = false;
  }

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
</script>

<div class="side-by-side">
  {#if activeGroupOriginal.length > 0}
    <div class="text-block">
      <div class="header-row">
        <div class="card-title-small">Transcription</div>
        {#if auth.canEdit && activeSegment}
          {#if !editTranscript}
            <button class="edit-btn" onclick={() => editTranscript = true} title="Edit transcription">
              <Pencil size={14} />
            </button>
          {:else}
            <div class="edit-actions">
              <button class="edit-btn cancel" onclick={() => editTranscript = false} title="Cancel">
                <X size={14} />
              </button>
              <button class="edit-btn save" onclick={() => saveGroup(activeGroupOriginal, typeTranscript)} title="Save">
                <Check size={14} />
              </button>
            </div>
          {/if}
        {/if}
      </div>

      <p class="subtitle-content">
        {#each activeGroupOriginal as item}
          <span
            class="subtitle-span {item === currentSubtitle ? 'highlighted' : ''}" 
            onclick={() => mediaElement && jumpToTime(mediaElement, item.start)}
            role="button"
            tabindex="0"
            onkeydown={() => {}}
          >
            {#if editTranscript}
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
  {/if}
  {#if activeGroupTranslation.length > 0}
  <div class="text-block">
    <div class="header-row">
      <div class="card-title-small">Translation</div>
      {#if auth.canEdit && activeSegment}
        {#if !editTranslation}
          <button class="edit-btn" onclick={() => editTranslation = true} title="Edit translation">
            <Pencil size={14} />
          </button>
        {:else}
          <div class="edit-actions">
            <button class="edit-btn cancel" onclick={() => editTranslation = false} title="Cancel">
              <X size={14} />
            </button>
            <button class="edit-btn save" onclick={() => saveGroup(activeGroupTranslation, typeTranslation)} title="Save">
              <Check size={14} />
            </button>
          </div>
        {/if}
      {/if}
    </div>

    <p class="subtitle-content">
      {#each activeGroupTranslation as item}
        <span
          class="subtitle-span {item === currentSubtitleEn ? 'highlighted' : ''}"
          onclick={() => mediaElement && jumpToTime(mediaElement, item.start)}
          role="button"
          tabindex="0"
          onkeydown={() => {}}
        >
          {#if editTranscript}
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
