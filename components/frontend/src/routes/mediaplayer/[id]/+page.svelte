<script lang="ts">
  import DebateHeader from "$lib/components/DebateHeader.svelte";
  import MediaPlayer from "$lib/components/MediaPlayer.svelte";
  import SegmentList from "$lib/components/SegmentList.svelte";
  import SegmentDisplay from "$lib/components/SegmentDisplay.svelte";
  import SpeakerDisplay from "$lib/components/SpeakerDisplay.svelte";
  import DebateToolBar from "$lib/components/DebateToolBar.svelte";

  import type { PageData } from './$types';
  import type { components } from '$lib/api/schema';

  type Speaker = components['schemas']['Speaker'];
  type Segment = components['schemas']['Segment'];

  interface Props { data: PageData; }
  let { data }: Props = $props();

  // --- 1. State ---
  let debate = $state(data.metadata.debate);
  let speakers = $state<Speaker[]>(data.metadata.speakers || []);
  let segments = $state<Segment[]>(data.metadata.segments || []);

  // --- 2. Derived Constants ---
  const mediaUrl = $derived(data.signedUrls?.signedMediaUrl);
  const downloadUrls = $derived(data.signedUrls?.signedUrls || []);
  const mediaId =  $derived(data.mediaId);
  const term = $derived(data.term);

  // --- 3. PLAYER STATE ---
  let mediaElement = $state<HTMLVideoElement>();
  let currentTime = $state(0);

  // Simple helper
  function findCurrentSegment(time: number) {
      return segments.find(s => time >= s.start && time <= s.end);
  }

  // Reactive Derived Values
  // These update automatically whenever 'currentTime' changes
  let currentSegment = $derived(findCurrentSegment(currentTime));
  let currentSpeaker = $derived(
      currentSegment ? speakers.find(s => s.speaker_id === currentSegment.speaker_id) : undefined
  );

  // --- 5. Sync on Navigation ---
  $effect(() => {
    console.log("in effect");
    debate = data.metadata.debate;
    speakers = data.metadata.speakers || [];
    segments = data.metadata.segments || [];

    if (data.start) {
      currentTime = data.start;
    }
  });
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

<DebateHeader {debate} />

<div class="video-layout">

  <div class="col-md-3 segment-container">
    <SegmentList
      mediaElement={mediaElement}
      segments={segments}
      speakers={speakers}
      activeSpeaker={currentSpeaker}
      activeSegment={currentSegment}
    />
  </div>

  <div class="col-md-3 speaker-container">
    <SpeakerDisplay
      speakers={speakers}
      activeSpeaker={currentSpeaker}
      mediaId={mediaId}
    />
  </div>

  <div class="col-md-6 video-container">
    <MediaPlayer
      mediaUrl={mediaUrl || ''}
      bind:mediaElement
      bind:currentTime={currentTime} />
  </div>
</div>

<DebateToolBar {downloadUrls} />

<SegmentDisplay
  currentTime={currentTime}
  activeSegment={currentSegment}
  mediaId={mediaId}
  mediaElement={mediaElement}
  term={term}
/>

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
