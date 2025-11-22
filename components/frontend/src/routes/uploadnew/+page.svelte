<script lang="ts">
  import { invalidateAll } from '$app/navigation';
  import { FileIcon, UploadCloud, CheckCircle, AlertCircle, Loader2 } from 'lucide-svelte';

  // --- STATE ---
  // We use Svelte 5 runes for state management
  let files = $state<FileList>();
  let status = $state<'idle' | 'preparing' | 'uploading' | 'processing' | 'success' | 'error'>('idle');
  let progress = $state(0); 
  let errorMessage = $state<string | null>(null);

  // Derived state for easier access
  let file = $derived(files?.[0]);

  // --- HELPERS ---

  /**
   * Uploads file to S3 using XMLHttpRequest to track percentage progress.
   * (Standard fetch does not support upload progress tracking)
   */
  function uploadToS3(url: string, fields: Record<string, string>, file: File): Promise<void> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const formData = new FormData();

      // AWS S3 requires fields to be appended BEFORE the file
      Object.entries(fields).forEach(([k, v]) => formData.append(k, v));
      formData.append('file', file);

      xhr.open('POST', url);

      // Track Upload Progress
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          progress = Math.round((e.loaded / e.total) * 100);
        }
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve();
        } else {
          // Try to parse XML error from S3 if possible, otherwise generic text
          reject(`S3 Upload Failed: ${xhr.status}`);
        }
      };

      xhr.onerror = () => reject('Network Error during S3 Upload');
      xhr.send(formData);
    });
  }

  // --- MAIN HANDLER ---

  async function handleUpload() {
    if (!file) return;

    try {
      errorMessage = null;
      status = 'preparing';
      progress = 0;

      // 1. Get Presigned URL from your Backend
      // Ensure you have an endpoint at /api/upload/presign or change this URL
      const presignRes = await fetch('/api/upload/presign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: file.name, contentType: file.type })
      });
      
      if (!presignRes.ok) {
        const err = await presignRes.json();
        throw new Error(err.detail || 'Failed to get upload permissions');
      }

      const { postUrl, fields, s3Key } = await presignRes.json();

      // 2. Upload directly to S3
      status = 'uploading';
      await uploadToS3(postUrl, fields, file);

      // 3. Register Job in Backend
      status = 'processing';
      const jobRes = await fetch('/api/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ s3Key, title: file.name })
      });

      if (!jobRes.ok) throw new Error('Failed to register processing job');

      // 4. Success
      status = 'success';
      files = undefined; // Clear input
      await invalidateAll(); // Refresh data

    } catch (err: any) {
      status = 'error';
      errorMessage = err.message || 'Unknown error occurred';
      console.error(err);
    }
  }
</script>

<svelte:head>
  <title>Upload Video</title>
</svelte:head>

<section class="flex flex-col items-center justify-center min-h-[60vh] p-4">
  
  <div class="w-full max-w-2xl border-2 border-dashed border-slate-300 rounded-xl p-8 bg-slate-50 transition-all"
       class:border-blue-500={status === 'uploading'}>
    
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-slate-800 flex items-center gap-2">
        <UploadCloud class="w-8 h-8 text-blue-600" />
        Video Upload
      </h1>
    </div>

    <div class="space-y-6">
      <label class="block cursor-pointer group">
        <input 
          bind:files 
          type="file" 
          accept="video/*" 
          class="hidden" 
          disabled={status === 'uploading' || status === 'processing'}
        />
        
        <div class="border-2 border-slate-200 rounded-lg p-6 text-center bg-white group-hover:border-blue-400 transition-colors">
          {#if file}
            <div class="font-medium text-lg text-blue-700">{file.name}</div>
            <div class="text-sm text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</div>
          {:else}
            <span class="text-slate-500 font-medium">Click to select a video file</span>
          {/if}
        </div>
      </label>

      {#if status !== 'idle'}
        <div class="bg-white rounded-lg p-4 border border-slate-200 shadow-sm space-y-3">
          
          {#if status === 'preparing'}
            <div class="flex items-center gap-3 text-blue-600 animate-pulse">
              <Loader2 class="animate-spin w-5 h-5" />
              <span>Requesting permissions...</span>
            </div>
          {/if}

          {#if status === 'uploading'}
            <div class="space-y-1">
              <div class="flex justify-between text-sm font-semibold text-slate-700">
                <span>Uploading to S3...</span>
                <span>{progress}%</span>
              </div>
              <div class="w-full bg-slate-200 rounded-full h-2.5">
                <div class="bg-blue-600 h-2.5 rounded-full transition-all duration-200" style="width: {progress}%"></div>
              </div>
            </div>
          {/if}

          {#if status === 'processing'}
            <div class="flex items-center gap-3 text-purple-600">
              <Loader2 class="animate-spin w-5 h-5" />
              <span>Queueing job...</span>
            </div>
          {/if}

          {#if status === 'success'}
            <div class="flex items-center gap-3 text-green-600 bg-green-50 p-3 rounded">
              <CheckCircle class="w-6 h-6" />
              <span class="font-bold">Upload Complete! Job started.</span>
            </div>
            <button class="text-sm text-slate-500 underline mt-2" onclick={() => status = 'idle'} type="button">
              Upload another?
            </button>
          {/if}

          {#if status === 'error'}
            <div class="flex items-center gap-3 text-red-600 bg-red-50 p-3 rounded">
              <AlertCircle class="w-6 h-6" />
              <span class="font-bold">Error: {errorMessage}</span>
            </div>
            <button class="text-sm text-slate-500 underline mt-2" onclick={() => status = 'idle'} type="button">
              Try again
            </button>
          {/if}
        </div>
      {/if}

      {#if status === 'idle' || status === 'error'}
        <button
          class="w-full py-3 px-4 bg-slate-800 text-white font-bold rounded-lg hover:bg-slate-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          disabled={!file}
          onclick={handleUpload}
          type="button"
        >
          {#if !file} Select File First {:else} Start Upload {/if}
        </button>
      {/if}
      
    </div>
  </div>
</section>

<style>
    section {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        flex: 0.6;
    }

    .links {
        display: flex;
        flex-direction: row;
        justify-content: end;
        width: 100%;
        align-items: end;
        gap: 2rem;
    }

    h1 {
        font-family: var(--body-font);
        font-size: 36px;
        color: var(--primary-dark-color);
        line-height: 1;
        font-weight: bold;
    }

    .info {
        border: 2px dashed var(--primary-dark-color);
        padding: 50px;
        color: var(--text-color);
        margin-top: 1rem;
        border-radius: 10px;
        width: 90%;
        max-width: 800px;
        justify-content: start;
        align-items: start;
        display: flex;
        flex-direction: column;
        gap: 2rem;
    }

    /* Custom Input Style */
    .input {
        border: 1px solid var(--primary-dark-color);
        padding: 10px;
        border-radius: 5px;
        width: 100%;
        cursor: pointer;
    }

    /* Primary Button Style to ensure it works without Skeleton's full class set */
    .btn {
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: bold;
        transition: background-color 0.2s;
        border: none;
        cursor: pointer;
    }

    .variant-filled-primary {
        background-color: var(--secondary-color);
        color: white;
    }

    .variant-filled-secondary {
        background-color: #6c757d; /* A neutral gray */
        color: white;
    }

    .btn:disabled {
        background-color: #ccc;
        cursor: not-allowed;
        opacity: 0.6;
    }
</style>
