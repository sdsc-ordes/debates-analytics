<script lang="ts">
  import VideoUploader from '$lib/components/VideoUploader.svelte';
  import ProcessingStatus from '$lib/components/ProcessingStatus.svelte';

  // This state determines which component is shown
  let activeMediaId = $state<string | null>(null);

  function handleUploadComplete(id: string) {
    activeMediaId = id; // Switch to status view
  }

  function handleReset() {
    activeMediaId = null; // Switch back to upload view
  }
</script>

<svelte:head>
  <title>Upload Video</title>
</svelte:head>

<section>
  <div class="info upload-card">

    {#if activeMediaId}
      <ProcessingStatus
        mediaId={activeMediaId}
        onReset={handleReset}
      />
    {:else}
      <VideoUploader
        onComplete={handleUploadComplete}
      />
    {/if}

  </div>
</section>

<style>
  section {
    display: flex; justify-content: center; padding-top: 4rem;
  }
  .upload-card {
    background: white; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    width: 100%; max-width: 28rem; padding: 1.5rem;
  }
</style>
