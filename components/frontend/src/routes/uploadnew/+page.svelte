<script lang="ts">
  import { logger } from '$lib/utils/logger';
  import { FileIcon } from 'lucide-svelte';
  // The files variable is bound to the input's FileList
  let files: FileList | undefined = $state();

  let errorMessage: string | null = $state(null);
  let uploadStatus: 'idle' | 'fetching-url' | 'uploading' | 'success' | 'error' = $state('idle');
  let uploadMessage: string | null = $state(null);
  
  // Removed uploadedUrls state as it is no longer strictly needed for the upload mechanism

  /**
   * Handles the entire 3-step upload process on button click:
   * 1. Get Presigned URL from Backend (FastAPI)
   * 2. HTTP PUT file directly to S3
   * 3. Register job with SvelteKit server action
   */
  async function handleFullUpload() {
    if (!files || files.length === 0) {
        errorMessage = "Please select a file first.";
        return;
    }

    const file = files[0];
    
    // Reset state and set initial status
    errorMessage = null;
    uploadStatus = 'fetching-url';
    uploadMessage = `1/3: Requesting secure S3 path for ${file.name}...`;

    // --- STEP 1: Get Presigned Upload URL from Backend (FastAPI) ---
    const endpoint = '/api/upload'; 
    try {
        const urlResponse = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ "filename": file.name })
        });

        if (!urlResponse.ok) {
            const errorData = await urlResponse.json();
            const detailMessage = errorData.detail?.[0]?.msg || errorData.error || JSON.stringify(errorData);
            errorMessage = `URL Fetch Failed: ${urlResponse.status}. Detail: ${detailMessage}`;
            logger.error({ status: urlResponse.status, body: errorData }, errorMessage);
            uploadStatus = 'error';
            return;
        }
        
        const data = await urlResponse.json();
        const { uploadUrl, jobId, s3Key } = data;
        
        if (!uploadUrl || !jobId) {
            errorMessage = "Backend response missing upload URL or Job ID.";
            uploadStatus = 'error';
            return;
        }

        // --- STEP 2: Upload the File Directly to S3 using HTTP PUT ---
        uploadStatus = 'uploading';
        uploadMessage = `2/3: Uploading ${file.name} directly to S3...`;
        
        const s3Response = await fetch(uploadUrl, {
            method: 'PUT',
            headers: { 'Content-Type': file.type },
            body: file
        });

        if (!s3Response.ok) {
            errorMessage = `S3 upload failed. Status: ${s3Response.status}. Check S3 permissions.`;
            logger.error("S3 Upload Failed.", { status: s3Response.status, statusText: s3Response.statusText });
            uploadStatus = 'error';
            return;
        }
        
        // --- STEP 3: Trigger Server Action (registerJob) ---
        uploadStatus = 'fetching-url'; // Reusing this status for the low-latency job registration step
        uploadMessage = `3/3: File uploaded. Initiating backend processing...`;

        const formData = new FormData();
        formData.append('jobId', jobId);
        formData.append('s3Key', s3Key);
        formData.append('title', file.name); 

        const registerResponse = await fetch('?/registerJob', {
            method: 'POST',
            body: formData,
        });
        
        const actionResult = await registerResponse.json();

        if (registerResponse.ok && actionResult.type !== 'failure') {
            uploadStatus = 'success';
            uploadMessage = actionResult.data.message;
            logger.success("Job registered.", { jobId });
            // Clear files and reload to update job list
            files = undefined;
            window.location.reload(); 
        } else {
            uploadStatus = 'error';
            errorMessage = `Upload successful, but job registration failed: ${actionResult.data?.message || 'Server error.'}`;
            logger.error("Job registration failed.", { jobId, result: actionResult });
        }


    } catch (e) {
        uploadStatus = 'error';
        errorMessage = `Fatal network error during process: ${e}`;
        logger.error("Fatal Network Error.", { error: e });
    }
  }
</script>

<svelte:head>
    <title>Upload</title>
    <meta name="description" content="File upload" />
</svelte:head>

<section>
    <div class="info">
        
        <div class="links">
             <a
                href="YOUR_GITHUB_LINK_HERE"
                aria-label="View Project on GitHub"
                title="View Project on GitHub"
            >
                <!-- Using lucide icon -->
                <FileIcon class="size-6 text-[var(--primary-dark-color)]" />
            </a>
        </div>

        <h1>Video Upload</h1>

        <div class="w-full space-y-4">
            
            <!-- File Input Section -->
            <label for="many" class="label block">
                <span class="text-lg font-bold">1. Select Media File</span>
            </label>
            <input 
                accept="video/*,audio/*" 
                bind:files 
                id="many" 
                multiple 
                type="file" 
                class="input"
            />
            
            <!-- Status and Submit Button -->
            <div class="flex flex-col items-start gap-3 pt-4">
                
                <!-- Status Message -->
                {#if uploadStatus !== 'idle' || errorMessage}
                    <p class="p-3 rounded-lg text-sm font-semibold w-full"
                        class:bg-blue-100={uploadStatus === 'fetching-url'}
                        class:bg-yellow-100={uploadStatus === 'uploading'}
                        class:bg-red-500={uploadStatus === 'error' || errorMessage}
                        class:text-white={uploadStatus === 'error' || errorMessage}
                        class:text-blue-900={uploadStatus === 'fetching-url'}
                        class:text-yellow-900={uploadStatus === 'uploading'}
                    >
                        {#if errorMessage}
                            ERROR: {errorMessage}
                        {:else}
                            {uploadMessage}
                        {/if}
                    </p>
                {/if}

                <!-- Upload Button -->
                <button
                    type="button"
                    class="btn w-full max-w-sm"
                    class:variant-filled-primary={files && files.length > 0 && uploadStatus !== 'uploading' && uploadStatus !== 'fetching-url'}
                    class:variant-filled-secondary={!(files && files.length > 0 && uploadStatus !== 'uploading' && uploadStatus !== 'fetching-url')}
                    disabled={!files || files.length === 0 || uploadStatus === 'uploading' || uploadStatus === 'fetching-url'}
                    onclick={handleFullUpload}
                >
                    {#if uploadStatus === 'uploading'}
                        Uploading...
                    {:else if uploadStatus === 'fetching-url'}
                        Initializing...
                    {:else if files && files.length > 0}
                        2. Upload and Start Job
                    {:else}
                        Select File to Enable Upload
                    {/if}
                </button>
            </div>
            
        </div>
        
        <!-- File Display (Manual List) -->
        {#if files && files.length > 0}
            <h3 class="text-base font-semibold pt-4">Selected File:</h3>
            {#each Array.from(files) as file}
                <p class="text-sm">
                    **Name:** {file.name} | **Type:** {file.type} | **Size:** {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
            {/each}
        {/if}
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
