<script lang="ts">
  interface Props {
    mediaUrl: string;
    mediaType?: 'video' | 'audio';
    currentTime?: number;
    mediaElement?: HTMLMediaElement;
  }

  let {
    mediaUrl,
    mediaType,
    currentTime = $bindable(0),
    mediaElement = $bindable()
  }: Props = $props();

console.log("MediaPlayer initialized with URL:", mediaUrl);
</script>

<div class="media-container">
  {#if mediaType === "video"}
    <video
      class="media"
      src={mediaUrl}
      bind:this={mediaElement}
      bind:currentTime={currentTime}
      controls
      playsinline
    >
      <source src={mediaUrl} type="{mediaType}/mp4" />
      Your browser does not support the video tag.
    </video>
  {:else if mediaType === "audio"}
    <audio
      class="media"
      bind:this={mediaElement}
      bind:currentTime={currentTime}
      controls
      playsinline
    >
      <source src={mediaUrl} type="{mediaType}/wav" />
      Your browser does not support the audio tag.
    </audio>
  {:else}
    <div class="placeholder">
        <p>Waiting for media source...</p>
    </div>
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
