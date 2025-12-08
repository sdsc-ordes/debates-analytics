<script lang="ts">
  import DebateHeader from "$lib/components/DebateHeader.svelte";
  import type { PageData } from './$types';
  import type { components } from '$lib/api/schema';
  type MetadataResponse = components['schemas']['MetadataResponse'];

  interface Props {
    data: PageData;
  }

  let { data }: Props = $props();

  let metadata: MetadataResponse = $derived(data.metadata);
  const debate = metadata.debate;
  console.log("data", data);
</script>

<svelte:head>
  <title>VideoPlayer Page</title>
  <meta name="description" content="Videoplayer" />
  <style>
    :root {
      --tadashi_svelte_notifications_width: 300px;
    }
  </style>
</svelte:head>

<DebateHeader { debate } />

<style>
.video-layout {
  display: flex;
  gap: 1rem; /* Adds spacing between elements */
  justify-content: center;
  align-items: flex-start; /* Aligns everything to the top */
  width: 100%;
  height:30vh;
  padding-bottom: 1rem;
}

.segment-container {
  flex: 1;
  max-width: 25%;
  max-height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.speaker-container {
  flex: 1;
  max-width: 25%;
  max-height: 30vh;
  max-height: 100%;
}

.video-container {
  flex: 2;
  max-width: 40%;
  max-height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}
</style>
