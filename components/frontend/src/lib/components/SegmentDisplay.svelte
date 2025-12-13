<script lang="ts">
  import { canEdit } from "$lib/stores/auth";
  import { jumpToTime } from "$lib/utils/mediaStartUtils";
  import type { components } from '$lib/api/schema';
  import { client } from '$lib/api/client';

  type Subtitle = components['schemas']['Subtitle'];
  type Segment = components['schemas']['Segment'];

  // Define types locally if not exported from schema
  const typeTranscript = "Transcript"
  const typeTranslation = "Translation"

  interface Props {
    activeSegment?: Segment;
    mediaElement?: HTMLMediaElement;
    mediaId: string;
    currentTime: number,
  }

  let {
    activeSegment,
    mediaElement,
    mediaId,
    currentTime,
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
    console.log(payload);

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
</script>

<div class="side-by-side">
  {#if activeGroupOriginal.length > 0}
    <div class="text-block">
      <div class="header-row">
        <div class="card-title-small">Transcription</div>
        {#if $canEdit && activeSegment}
          {#if !editTranscript}
            <button class="secondary-button" onclick={() => editTranscript = true}>Edit</button>
          {:else}
            <button class="secondary-button" onclick={() => editTranscript = false}>Cancel</button>
            <button class="secondary-button" onclick={() => saveGroup(activeGroupOriginal, typeTranscript)}>Save</button>
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
              {item.text}{" "}
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
      {#if $canEdit && activeSegment}
        {#if !editTranslation}
          <button class="secondary-button" onclick={() => editTranslation = true}>Edit</button>
        {:else}
          <button class="secondary-button" onclick={() => editTranslation = false}>Cancel</button>
          <button class="secondary-button" onclick={() => saveGroup(activeGroupTranslation, typeTranslation)}>Save</button>
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
          {#if editTranslation}
            <textarea
              bind:value={item.text}
              class="editable-textarea"
              rows="2"
              onclick={(e) => e.stopPropagation()}
            ></textarea>
          {:else}
            {item.text}{" "}
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

  .highlighted {
    color: var(--secondary-color);
  }

  .editable-textarea {
    width: 100%;
    height: 50px;
  }

  .highlighted-textarea {
    border: 2px solid var(--secondary-color);
  }

  p {
    margin: 0;
    padding: 0;
    word-wrap: break-word;
  }

</style>
