<script lang="ts">
  import { onMount } from 'svelte';
  import { Loader, CircleCheck, CircleAlert } from 'lucide-svelte';

  // Props:
  // - mediaId: The ID to poll
  // - onReset: Function to go back to the uploader when done
  let { mediaId, onReset } = $props<{ mediaId: string, onReset: () => void }>();

  // State
  let processingStep = $state('Initializing...');
  $inspect("at setpe", processingStep)
  let isFinished = $state(false);
  let error = $state<string | null>(null);

  async function pollStatus() {
    try {
      // Loop until finished or error
      while (!isFinished && !error) {
        console.log("monitoring")

        // Call your SvelteKit Proxy Route (which forwards to Python)
        // Ensure your Python main.py has prefix="/metadata" for the router
        const res = await fetch(`/api/upload/status/${mediaId}`);

        if (res.status === 404) {
           // Job might not be in DB yet, wait and retry
           await new Promise(r => setTimeout(r, 2000));
           continue;
        }

        if (!res.ok) throw new Error("Failed to fetch status");

        const data = await res.json();

        // 1. Update UI Text
        // We prefer 'progress' (from Redis) because it's granular (e.g. "Translating")
        if (data.progress) {
            processingStep = data.progress.charAt(0).toUpperCase() + data.progress.slice(1);
        } else {
            processingStep = data.status;
        }

        // 2. Check Success
        // Matches the "status" set in your Python task
        if (data.status === 'transcribing_completed' || data.status === 'success') {
            isFinished = true;
            return;
        }

        // 3. Check Failure
        if (data.status === 'failed' || data.job_state === 'failed') {
            throw new Error(data.error || "Processing failed on server");
        }

        // 4. Wait 2 seconds before next check
        await new Promise(r => setTimeout(r, 2000));
      }
    } catch (e: any) {
      error = e.message;
    }
  }

  // Start polling as soon as this component appears
  onMount(() => {
    pollStatus();
  });
</script>

<h1>Processing Status</h1>

<div class="status-box">
  {#if error}
    <div class="status-row error">
      <CircleAlert class="icon-small text-red-500" />
      <span>{error}</span>
    </div>
    <button class="link-button" onclick={onReset}>Try Again</button>

  {:else if isFinished}
    <div class="status-row success">
      <CircleCheck class="icon-small text-green-500" />
      <div>
         <strong>Processing Complete!</strong>
         <p class="text-xs text-gray-500">Media ID: {mediaId}</p>
      </div>
    </div>
    <button class="button-primary mt-4" onclick={onReset}>Upload Another</button>

  {:else}
    <div class="status-col">
      <div class="status-row loading">
        <Loader class="animate-spin icon-small text-blue-500" />
        <span class="font-medium text-lg">{processingStep}</span>
      </div>

      <div class="progress-track indeterminate mt-2">
        <div class="progress-fill-indeterminate"></div>
      </div>

      <p class="text-xs text-gray-400 mt-2 text-center">ID: {mediaId}</p>
    </div>
  {/if}
</div>

<style>
  .status-box { padding: 1rem; }
  .status-col { display: flex; flex-direction: column; width: 100%; }
  .status-row { display: flex; align-items: center; gap: 0.75rem; justify-content: center; }
  .icon-small { width: 1.5rem; height: 1.5rem; }

  .button-primary {
    background-color: #3b82f6; color: white; padding: 0.5rem 1rem;
    border-radius: 6px; border: none; cursor: pointer; width: 100%;
  }

  /* Indeterminate Animation */
  .progress-track.indeterminate {
    width: 100%; height: 6px; background: #e5e7eb; border-radius: 99px; overflow: hidden; position: relative;
  }
  .progress-fill-indeterminate {
    height: 100%; width: 50%; background: #3b82f6; position: absolute;
    animation: indeterminate 1.5s infinite linear;
  }
  @keyframes indeterminate {
    0% { left: -50%; }
    100% { left: 100%; }
  }
</style>