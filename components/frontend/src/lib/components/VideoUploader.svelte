<script lang="ts">
  import { invalidateAll } from '$app/navigation';
  import { client } from '$lib/api/client';
  import { CloudUpload, CircleCheck, CircleAlert, Loader, ArrowLeft } from 'lucide-svelte';

  let files = $state<FileList>();
  let status = $state<'idle' | 'preparing' | 'uploading' | 'processing' | 'success' | 'error'>('idle');
  let progress = $state(0);
  let errorMessage = $state<string | null>(null);
  let file = $derived(files?.[0]);
  let assignedMediaId = $state<string | null>(null);

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
    if (!checkFileType(file)) {
      errorMessage = 'Invalid file type. Please upload an MP4 video or WAV audio file.';
      status = 'error';
      return;
    }

    try {
      errorMessage = null;
      status = 'preparing';
      progress = 0;

      // Get Presigned URL
      const { data: presignData, error: presignError } = await client.POST("/ingest/get-presigned-post", {
        body: {
            filename: file.name,
            contentType: file.type
        }
      });

      if (presignError || !presignData) {
        throw new Error("Failed to get upload permissions");
      }

      const {
          postUrl: url,
          fields,
          mediaId,
          s3Key,
      } = presignData as any;

      assignedMediaId = mediaId;

      status = 'uploading';
      await uploadToS3(url, fields, file);

      status = 'processing';

      const { error: processError } = await client.POST("/ingest/process", {
          body: {
              media_id: mediaId,
              s3_key: s3Key,
              title: file.name,
              file_type: file.type,
          }
      });

      if (processError) {
          throw new Error("Upload successful, but failed to start processing job.");
      }

      status = 'success';
      files = undefined;
      await invalidateAll();

    } catch (err: any) {
      status = 'error';
      errorMessage = err.message || 'Unknown error occurred';
      console.error(err);
    }
  }

  function checkFileType(file: File): boolean {
    const allowedTypes = ['video/mp4', 'audio/wav'];
    return allowedTypes.includes(file.type);
  }
</script>

<section class="page-layout">
  <div class="upload-card">
    <a href="/dashboard" class="back-link">
      <ArrowLeft size={16} />
      Back to Dashboard
    </a>

    <header>
      <CloudUpload size={28} color="var(--primary-color)" />
      <h1>Upload Media</h1>
      <p>Select an MP4 or WAV file to add to your media library</p>
    </header>

    <label class="drop-zone" class:disabled={status === 'uploading' || status === 'processing' || status === 'success'}>
      <input bind:files type="file" accept="video/mp4 audio/wav" disabled={status === 'uploading' || status === 'processing' || status === 'success'} />
      {#if file}
        <strong>{file.name}</strong>
        <small>{(file.size / 1024 / 1024).toFixed(2)} MB</small>
      {:else}
        <CloudUpload size={40} color="#9ca3af" />
        <span>Click to select a video or audio file in mp4 or wav format.</span>
      {/if}
    </label>

    {#if status === 'preparing' || status === 'processing'}
      <div class="status loading">
        <Loader class="animate-spin" size={18} />
        {status === 'preparing' ? 'Requesting permissions...' : 'Queueing job...'}
      </div>
    {/if}

    {#if status === 'uploading'}
      <div class="status">
        <div class="progress-label">Uploading... <strong>{progress}%</strong></div>
        <div class="progress-track"><div class="progress-fill" style="width: {progress}%"></div></div>
      </div>
    {/if}

    {#if status === 'success'}
      <div class="status success">
        <CircleCheck size={18} /> Upload Complete!
      </div>
      <small class="media-id">Media ID: <code>{assignedMediaId}</code></small>
      <a href="/dashboard" class="button-primary">Go to Library</a>
    {/if}

    {#if status === 'error'}
      <div class="status error">
        <CircleAlert size={18} /> {errorMessage}
      </div>
      <button class="link-button" onclick={() => status = 'idle'} type="button">Try again</button>
    {/if}

    {#if file && (status === 'idle' || status === 'error')}
      <button class="button-primary" disabled={!file} onclick={handleUpload} type="button">
        Upload mediafile
      </button>
    {/if}
  </div>
</section>

<style>
  .page-layout { display: flex; justify-content: center; padding: 2rem 1rem; }
  .upload-card { background: #fff; width: 100%; max-width: 480px; border-radius: 12px; padding: 1.5rem; border: 1px solid #eaeaea; }

  .back-link { display: inline-flex; align-items: center; gap: 6px; color: grey; font-size: 13px; text-decoration: none; margin-bottom: 1rem; }
  .back-link:hover { color: var(--primary-color); }

  header { text-align: center; margin-bottom: 1.5rem; }
  header h1 { font-size: 22px; padding: 0; margin: 0.5rem 0 0.25rem; }
  header p { color: grey; font-size: 14px; margin: 0; }

  .drop-zone { display: flex; flex-direction: column; align-items: center; gap: 0.5rem; border: 2px dashed #d1d5db; border-radius: 10px; padding: 2rem; cursor: pointer; background: #fafafa; margin-bottom: 1rem; }
  .drop-zone:hover:not(.disabled) { border-color: var(--primary-color); background: #f0f4ff; }
  .drop-zone.disabled { opacity: 0.6; cursor: not-allowed; }
  .drop-zone input { display: none; }
  .drop-zone strong { color: var(--primary-color); word-break: break-all; text-align: center; }
  .drop-zone small { color: grey; font-size: 13px; }

  .status { display: flex; align-items: center; gap: 8px; font-size: 14px; margin-bottom: 1rem; }
  .status.loading { color: var(--primary-color); }
  .status.success { color: #059669; }
  .status.error { color: #dc2626; }

  .progress-label { display: flex; justify-content: space-between; width: 100%; font-size: 14px; }
  .progress-track { height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; width: 100%; margin-top: 6px; }
  .progress-fill { height: 100%; background: var(--primary-color); transition: width 0.3s; }

  .media-id { display: block; text-align: center; color: grey; margin-bottom: 1rem; }
  .media-id code { color: var(--primary-color); }

  .button-primary { width: 100%; padding: 10px; text-align: center; text-decoration: none; display: block; }
  .link-button { background: none; border: none; color: var(--primary-color); cursor: pointer; font-size: 13px; text-decoration: underline; padding: 0; }

  :global(.animate-spin) { animation: spin 1s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>