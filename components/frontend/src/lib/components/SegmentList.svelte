<script lang="ts">
  import { formatTimeForDisplay, displaySpeaker } from "$lib/utils/displayUtils";
  import { jumpToTime } from "$lib/utils/mediaStartUtils";
  import type { components } from '$lib/api/schema';

  // Use the unified types from your schema
  type Segment = components['schemas']['Segment'];
  type Speaker = components['schemas']['Speaker'];

  interface Props {
    segments: Segment[];
    speakers: Speaker[];
    // We now accept just the current segment object directly
    activeSegment?: Segment;
    activeSpeaker?: Speaker;
    mediaElement?: HTMLVideoElement;
  }

  let {
    segments,
    speakers,
    activeSegment,
    activeSpeaker,
    mediaElement,
  }: Props = $props();

  // Helper to check if a specific segment is the active one
  function isCurrent(seg: Segment): boolean {
    return activeSegment?.segment_nr === seg.segment_nr;
  }
</script>

<div class="scrollable-container">
  <ol>
    {#each segments as segment}
      <li id="segment-{segment.segment_nr}">
        <div
          class="card text-center {isCurrent(segment) ? 'current' : 'other'}"
          onclick={() => mediaElement && jumpToTime(mediaElement, segment.start)}
          role="button"
          tabindex="0"
          onkeydown={(e) =>
            (e.key === "Enter" || e.key === " ") &&
            mediaElement && jumpToTime(mediaElement, segment.start)}
        >
          <div class="card-body">
            <div class="card-title-small" style="color: inherit;">
              {#if activeSpeaker }
              {@html displaySpeaker(segment.speaker_id || segment.speaker_id, speakers)}
              {/if}
            </div>

            <div class="date-time-item">
              <i
                class="fa fa-clock {isCurrent(segment) ? 'current' : 'other'}"
                aria-hidden="true"
              ></i>
              <small class="card-subtle {isCurrent(segment) ? 'current' : 'other'}">
                {formatTimeForDisplay(segment.start)} - {formatTimeForDisplay(segment.end)}
              </small>
            </div>
          </div>
        </div>
      </li>
    {/each}
  </ol>
</div>

<style>
  .scrollable-container {
    overflow-y: auto;
    max-height: 60vh;
    max-width: 100%;
  }
  ol li {
    list-style-type: none;
  }

  .card {
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    margin-bottom: 1rem;
  }
  .card-body {
    display: flex;
    flex-direction:row;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
  }

  /* Styles for the current speaker card */
  .card.current {
    color: var(--on-primary);
    background-color: var(--primary-dark-color);
  }

  .fa {
    font-size: 1rem;
    color: var(--primary-dark-color);
  }
  .fa.current {
    color: var(--on-primary);
  }

  .card-subtle {
    color: var(--primary-dark-color);
  }
  .card-subtle.current {
    color: var(--on-primary);
  }

</style>
