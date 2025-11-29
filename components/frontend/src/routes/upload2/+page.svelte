<script lang="ts">
  import VideoUploader from '$lib/components/VideoUploader.svelte';

  // State to track if we have a mediaId to process
  let activeMediaId = $state<string | null>(null);

  function handleUploadComplete(mediaId: string) {
    console.log("Upload complete! ID:", mediaId);
    activeMediaId = mediaId;
  }
</script>

<svelte:head>
  <title>Ingest Video</title>
</svelte:head>

<div class="page-container">
  {#if activeMediaId}
    <div class="success-message">
      <h2>Upload Successful</h2>
      <p>Media ID: {activeMediaId}</p>
      <p>Ideally, we would show a progress bar here now.</p>
      <button onclick={() => activeMediaId = null}>Upload Another</button>
    </div>
  {:else}
    <VideoUploader onComplete={handleUploadComplete} />
  {/if}
</div>

<style>
  .page-container {
    display: flex;
    justify-content: center;
    padding-top: 4rem;
    min-height: 100vh;
    background-color: #f9fafb;
  }
  .success-message {
    text-align: center;
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
  }
</style>
