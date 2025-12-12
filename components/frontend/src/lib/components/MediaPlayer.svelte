<script lang="ts">
  interface Props {
    mediaUrl: string;
    // 1. Add currentTime to the interface
    currentTime?: number; 
    mediaElement?: HTMLMediaElement;
  }

  let {
    mediaUrl,
    currentTime = $bindable(0),
    mediaElement = $bindable()
  }: Props = $props();

</script>

<div class="media-container">
  {#if mediaUrl}
    <video
      class="media"
      src={mediaUrl}
      bind:this={mediaElement}
      bind:currentTime={currentTime}
      controls
      playsinline
    >
      Your browser does not support the video tag.
    </video>
  {:else}
    <div class="placeholder">
        <p>Waiting for video source...</p>
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
