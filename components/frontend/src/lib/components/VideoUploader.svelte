<script lang="ts">
  import { invalidateAll } from '$app/navigation';
  import { client } from '$lib/api/client';
  import { CloudUpload, CircleCheck, CircleAlert, Loader } from 'lucide-svelte';

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

      console.log("Presign Data:", presignData);

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
          accept="video/mp4"
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
              <span>Upload Complete! Media ID: {assignedMediaId}</span>
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

      {#if file && (status === 'idle' || status === 'error')}
        <button
          class="button-primary full-width"
          disabled={!file}
          onclick={handleUpload}
          type="button"
        >
          Upload
        </button>
      {/if}

    </div>
  </div>
</section>