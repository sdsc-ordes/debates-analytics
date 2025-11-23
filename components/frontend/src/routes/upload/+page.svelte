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

      status = 'processing';
      await fetch('/api/process', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ jobId, s3Key, title: file.name })
      });

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
      <label class="drop-zone" class:disabled={status === 'uploading' || status === 'processing' || status === 'success'}>
        <input
          bind:files
          type="file"
          accept="video/*,audio/*"
          disabled={status === 'uploading' || status === 'processing' || status === 'success'}
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
                <span>Uploading...</span>
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
    /* --- Layout --- */
    section {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 60vh; /* Keeps it centered vertically */
        padding: 1rem;
    }

    /* --- The Main Card --- */
    .info {
        border: 2px dashed var(--primary-dark-color);
        background-color: white;
        color: var(--text-color);
        
        /* Modest Sizing */
        width: 100%;
        max-width: 480px; /* Reduced from 800px */
        padding: 2rem;    /* Reduced from 50px */
        border-radius: 12px;
        
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
        align-items: center; /* Centers content inside card */
    }

    .header {
        display: flex;
        flex-direction: column; /* Stack icon on top of text */
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
    }

    h1 {
        font-family: var(--body-font);
        font-size: 1.75rem; /* Reduced size */
        color: var(--primary-dark-color);
        line-height: 1.2;
        font-weight: bold;
        margin: 0;
    }

    .content-wrapper {
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
        width: 100%;
    }

    /* --- Icons --- */
    :global(.icon-primary) {
        color: var(--secondary-color);
        width: 2.5rem;
        height: 2.5rem;
    }
    :global(.icon-small) {
        width: 1.25rem;
        height: 1.25rem;
    }
    :global(.animate-spin) {
        animation: spin 1s linear infinite;
    }
    @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

    /* --- File Drop Zone --- */
    .drop-zone {
        border: 1px solid var(--primary-dark-color);
        border-radius: 8px;
        padding: 2.5rem 1.5rem; /* Taller padding for clickable area */
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: center;
        background-color: #fff;
    }

    .drop-zone:hover {
        background-color: #f8fafc;
        box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.05);
    }

    .drop-zone input { display: none; }

    .drop-zone.disabled {
        opacity: 0.6;
        cursor: not-allowed;
        background-color: #f1f5f9;
    }

    .file-name {
        font-weight: bold;
        color: var(--secondary-color);
        font-size: 1rem;
        word-break: break-all; /* Prevents long filenames breaking layout */
    }

    .file-size {
        font-size: 0.8rem;
        color: gray;
        margin-top: 0.25rem;
    }

    .placeholder-text {
        color: var(--text-color);
        font-weight: 500;
        font-size: 0.95rem;
    }

    /* --- Status Box --- */
    .status-box {
        padding: 0.75rem 1rem;
        border-radius: 8px;
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        font-size: 0.9rem;
    }

    .status-row {
        display: flex;
        align-items: center;
        justify-content: center; /* Center status text */
        gap: 0.5rem;
        font-weight: 600;
    }

    .status-row.loading { color: var(--secondary-color); }
    .status-row.success { color: #16a34a; }
    .status-row.error { color: #dc2626; }

    /* --- Progress Bar --- */
    .status-col {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .progress-label {
        display: flex;
        justify-content: space-between;
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--primary-dark-color);
    }

    .progress-track {
        width: 100%;
        height: 6px; /* Thinner */
        background-color: #e2e8f0;
        border-radius: 99px;
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
        color: white;
        border: none;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        font-size: 0.95rem;
        transition: opacity 0.2s;
        width: 100%;
    }

    .button-primary:hover { opacity: 0.9; }
    .button-primary:disabled { background-color: #cbd5e1; cursor: not-allowed; }

    .link-button {
        background: none;
        border: none;
        color: #64748b;
        text-decoration: underline;
        cursor: pointer;
        margin-top: 0.5rem;
        font-size: 0.8rem;
        width: 100%;
    }
</style>
