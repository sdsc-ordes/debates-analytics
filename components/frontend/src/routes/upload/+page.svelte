<script lang="ts">
  import { invalidateAll } from '$app/navigation';
  import { CloudUpload, CircleCheck, CircleAlert, Loader } from 'lucide-svelte';

  // --- LOGIC REMAINS EXACTLY THE SAME ---
  let files = $state<FileList>();
  let status = $state<'idle' | 'preparing' | 'uploading' | 'processing' | 'success' | 'error'>('idle');
  let progress = $state(0);
  let errorMessage = $state<string | null>(null);

  let file = $derived(files?.[0]);

  function uploadToS3(url: string, fields: Record<string, string>, file: File): Promise<void> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const formData = new FormData();

      Object.entries(fields).forEach(([k, v]) => formData.append(k, v));
      formData.append('file', file);

      xhr.open('POST', url);

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          progress = Math.round((e.loaded / e.total) * 100);
        }
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) resolve();
        else reject(`S3 Upload Failed: ${xhr.status}`);
      };

      xhr.onerror = () => reject('Network Error during S3 Upload');
      xhr.send(formData);
    });
  }

  async function handleUpload() {
    if (!file) return;

    try {
      errorMessage = null;
      status = 'preparing';
      progress = 0;

      const presignRes = await fetch('/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: file.name, contentType: file.type })
      });

      if (!presignRes.ok) {
        const err = await presignRes.json();
        throw new Error(err.detail || 'Failed to get upload permissions');
      }
      const response = await presignRes.json();

      const { postUrl, fields, jobId, s3Key } = response;
      
      status = 'uploading';
      await uploadToS3(postUrl, fields, file);

      status = 'success';
      files = undefined;
      await invalidateAll(); 

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

<section>
  <div class="info upload-card">
    
    <div class="header">
      <CloudUpload class="icon-primary" />
      <h1>Video Upload</h1>
    </div>

    <div class="content-wrapper">
      <label class="drop-zone" class:disabled={status === 'uploading' || status === 'processing'}>
        <input
          bind:files
          type="file"
          accept="video/*,audio/*"
          disabled={status === 'uploading' || status === 'processing'}
        />

        <div class="drop-zone-content">
          {#if file}
            <div class="file-name">{file.name}</div>
            <div class="file-size">{(file.size / 1024 / 1024).toFixed(2)} MB</div>
          {:else}
            <span class="placeholder-text">Click to select a video file</span>
          {/if}
        </div>
      </label>

      {#if status !== 'idle'}
        <div class="status-box">

          {#if status === 'preparing'}
            <div class="status-row loading">
              <Loader class="animate-spin icon-small" />
              <span>Requesting permissions...</span>
            </div>
          {/if}

          {#if status === 'uploading'}
            <div class="status-col">
              <div class="progress-label">
                <span>Uploading to S3...</span>
                <span>{progress}%</span>
              </div>
              <div class="progress-track">
                <div class="progress-fill" style="width: {progress}%"></div>
              </div>
            </div>
          {/if}

          {#if status === 'processing'}
            <div class="status-row loading">
              <Loader class="animate-spin icon-small" />
              <span>Queueing job...</span>
            </div>
          {/if}

          {#if status === 'success'}
            <div class="status-row success">
              <CircleCheck class="icon-small" />
              <span>Upload Complete! Job started.</span>
            </div>
            <button class="link-button" onclick={() => status = 'idle'} type="button">
              Upload another?
            </button>
          {/if}

          {#if status === 'error'}
            <div class="status-row error">
              <CircleAlert class="icon-small" />
              <span>Error: {errorMessage}</span>
            </div>
            <button class="link-button" onclick={() => status = 'idle'} type="button">
              Try again
            </button>
          {/if}
        </div>
      {/if}

      {#if status === 'idle' || status === 'error'}
        <button
          class="button-primary full-width"
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
    /* --- Layout & Typography --- */
    section {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        /* Matches Home page flex styling */
        flex: 0.6; 
        padding: 2rem;
    }

    h1 {
        font-family: var(--body-font);
        font-size: 36px;
        color: var(--primary-dark-color);
        line-height: 1;
        font-weight: bold;
        margin: 0;
    }

    /* --- The Main Card (Matches .info from Home) --- */
    .info {
        border: 2px dashed var(--primary-dark-color);
        padding: 50px;
        color: var(--text-color);
        margin-top: 1rem;
        border-radius: 10px;
        width: 90%;
        max-width: 800px;
        display: flex;
        flex-direction: column;
        gap: 2rem;
        background-color: white; /* Ensure readability */
    }

    .header {
        display: flex;
        align-items: center;
        gap: 1rem;
        justify-content: center;
        width: 100%;
        margin-bottom: 1rem;
    }

    .content-wrapper {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
        width: 100%;
    }

    /* --- Icons --- */
    /* Using global style for SVG icons to match theme */
    :global(.icon-primary) {
        color: var(--secondary-color);
        width: 2rem;
        height: 2rem;
    }
    :global(.icon-small) {
        width: 1.25rem;
        height: 1.25rem;
    }
    :global(.animate-spin) {
        animation: spin 1s linear infinite;
    }
    @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

    /* --- File Drop Zone (Input) --- */
    .drop-zone {
        border: 1px solid var(--primary-dark-color);
        border-radius: 5px; /* Matches input style */
        padding: 2rem;
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: center;
        background-color: #fff;
    }

    .drop-zone:hover {
        background-color: rgba(0,0,0,0.02);
        box-shadow: 0px 0px 5px rgba(0, 0, 0, 0.1);
    }

    .drop-zone input {
        display: none;
    }

    .drop-zone.disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }

    .file-name {
        font-weight: bold;
        color: var(--secondary-color);
        font-size: 1.1rem;
    }

    .file-size {
        font-size: 0.85rem;
        color: gray;
    }

    .placeholder-text {
        color: var(--text-color);
        font-weight: 500;
    }

    /* --- Status Box --- */
    .status-box {
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #ddd;
        background-color: #f9f9f9;
        font-size: 0.95rem;
    }

    .status-row {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-weight: bold;
    }

    .status-row.loading { color: var(--secondary-color); }
    .status-row.success { color: #16a34a; } /* Green */
    .status-row.error { color: #dc2626; }   /* Red */

    /* --- Progress Bar --- */
    .status-col {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .progress-label {
        display: flex;
        justify-content: space-between;
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--primary-dark-color);
    }

    .progress-track {
        width: 100%;
        height: 10px;
        background-color: #e5e5e5;
        border-radius: 5px;
        overflow: hidden;
    }

    .progress-fill {
        height: 100%;
        background-color: var(--secondary-color);
        transition: width 0.2s ease;
    }

    /* --- Buttons --- */
    .button-primary {
        background-color: var(--secondary-color);
        color: white; /* Assuming var(--on-primary) is white */
        border: none;
        padding: 12px 20px;
        border-radius: 8px; /* Matches Search form button radius */
        font-weight: bold;
        cursor: pointer;
        font-size: 1rem;
        transition: opacity 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }

    .button-primary:hover {
        opacity: 0.9;
    }

    .button-primary:disabled {
        background-color: #ccc;
        cursor: not-allowed;
    }

    .full-width {
        width: 100%;
    }

    .link-button {
        background: none;
        border: none;
        color: gray;
        text-decoration: underline;
        cursor: pointer;
        margin-top: 0.5rem;
        font-size: 0.85rem;
        width: 100%;
    }
</style>