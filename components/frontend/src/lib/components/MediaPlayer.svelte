<script lang="ts">
  import { onMount } from "svelte";
  import { onMediaTimeUpdate } from "$lib/utils/mediaTimeUpdate";
  import { jumpToTime } from "$lib/utils/mediaStartUtils";
  import type { TimeUpdateParameters } from "$lib/interfaces/mediaplayer.interface";
  import type {
    Subtitle,
    Speaker,
    Segment,
  } from "$lib/interfaces/metadata.interface";
  interface Props {
    startTime: number;
    timeUpdateParameters: TimeUpdateParameters;
    subtitles?: Subtitle[];
    subtitles_en?: Subtitle[];
    speakers?: Speaker[];
    segments?: Segment[];
    mediaElement: HTMLMediaElement;
    mediaUrl: string;
    media: any;
  }

  let {
    startTime,
    timeUpdateParameters = $bindable(),
    subtitles = [],
    subtitles_en = [],
    speakers = [],
    segments = [],
    mediaElement = $bindable(),
    mediaUrl,
    media
  }: Props = $props();

  function handleTimeUpdate() {
    timeUpdateParameters = onMediaTimeUpdate(
      mediaElement.currentTime,
      subtitles,
      subtitles_en,
      segments,
    );
  }

  onMount(async () => {
    if (startTime) {
      jumpToTime(mediaElement, startTime);
    }
  });
</script>

<div class="media-container">
  {#if media.type === "video"}
    <!-- svelte-ignore a11y_media_has_caption -->
    <video
      class="media"
      bind:this={mediaElement}
      ontimeupdate={handleTimeUpdate}
      controls
      disablePictureInPicture
    >
      <source src={mediaUrl} type="{media.type}/{media.format}" />
      Your browser does not support the video tag.
    </video>
  {:else if media.type === "audio"}
    <audio
      class="media"
      bind:this={mediaElement}
      ontimeupdate={handleTimeUpdate}
      controls
      autoplay
    >
      <source src={mediaUrl} type="{media.type}/{media.format}" />
      Your browser does not support the audio tag.
    </audio>
  {/if}
</div>

<style>
  .media {
    max-width: 100%;
    object-fit: contain;
  }

  .media-container {
    width: 100%;
    height: 100%; /* Forces it to respect the parent container */
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: hidden;
  }
</style>
