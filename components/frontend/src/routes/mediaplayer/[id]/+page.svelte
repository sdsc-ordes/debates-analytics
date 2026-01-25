<script lang="ts">
  import DebateHeader from "$lib/components/DebateHeader.svelte";
  import MediaPlayer from "$lib/components/MediaPlayer.svelte";
  import SegmentList from "$lib/components/SegmentList.svelte";
  import SegmentDisplay from "$lib/components/SegmentDisplay.svelte";
  import SpeakerDisplay from "$lib/components/SpeakerDisplay.svelte";
  import DebateToolBar from "$lib/components/DebateToolBar.svelte";
  import { Search } from 'lucide-svelte';

  import type { PageData } from './$types';
  import type { components } from '$lib/api/schema';

  type Speaker = components['schemas']['Speaker'];
  type Segment = components['schemas']['Segment'];

  interface Props { data: PageData; }
  let { data }: Props = $props();

  // --- state ---
  let debate = $state(data.metadata.debate);
  let speakers = $state<Speaker[]>(data.metadata.speakers || []);
  let segments = $state<Segment[]>(data.metadata.segments || []);
  let mediaElement = $state<HTMLVideoElement>();
  let currentTime = $state(0);

  let term = $state(data.term || '');
  let lastSegmentIndex = 0;

  // --- derived constants ---
  const mediaUrl = $derived(data.signedUrls?.signedMediaUrl);
  const downloadUrls = $derived(data.signedUrls?.signedUrls || []);
  const mediaId = $derived(data.mediaId);
  const mediaType = $derived(data.metadata.debate.media_type);


  let currentSegment = $derived.by(() => {
    const lastSeg = segments[lastSegmentIndex];
    if (lastSeg && currentTime >= lastSeg.start && currentTime <= lastSeg.end) {
      return lastSeg;
    }

    const index = segments.findIndex(s => currentTime >= s.start && currentTime <= s.end);

    if (index !== -1) {
      lastSegmentIndex = index;
      return segments[index];
    }
    return undefined;
  });
  let currentSpeaker = $derived(
      currentSegment ? speakers.find(s => s.speaker_id === currentSegment.speaker_id) : undefined
  );

  // Sync on Navigation ---
  $effect(() => {
    debate = data.metadata.debate;
    speakers = data.metadata.speakers || [];
    segments = data.metadata.segments || [];

    term = data.term || '';

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
      mediaType={mediaType || 'video'}
      bind:mediaElement
      bind:currentTime={currentTime} />
  </div>
</div>

<div class="controls-bar">
  <DebateToolBar {downloadUrls} />

  <div class="search-container">
    <span class="icon-wrapper">
      <Search size={16} />
    </span>
    <input
      type="search"
      placeholder="Search transcript..."
      bind:value={term}
      class="term-input"
    />
  </div>
</div>

<SegmentDisplay
  currentTime={currentTime}
  activeSegment={currentSegment}
  mediaId={mediaId}
  mediaElement={mediaElement}
  term={term}
/>

<style>
.controls-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 1rem 1rem 1rem;
}

.search-container {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f1f5f9;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.term-input {
  border: none;
  background: transparent;
  outline: none;
  font-size: 14px;
  color: #334155;
  width: 200px;
}

.icon-wrapper {
  color: #94a3b8;
  display: flex;
}

.video-layout {
  display: flex;
  gap: 1rem;
  justify-content: center;
  align-items: flex-start;
  width: 100%;
  padding-bottom: 1rem;
}

/* Ensure the search container doesn't get squashed */
.search-container {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f1f5f9;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  flex-shrink: 0;
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
