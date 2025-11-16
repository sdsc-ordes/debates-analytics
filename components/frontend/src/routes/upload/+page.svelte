<script lang="ts">
  import { logger } from '$lib/utils/logger';
  import { FileIcon } from 'lucide-svelte';
  
  // The files variable is bound to the input's FileList
  let files: FileList | undefined = $state();

  let errorMessage: string | null = $state(null);
  let uploadStatus: 'idle' | 'fetching-url' | 'uploading' | 'success' | 'error' = $state('idle');
  let uploadMessage: string | null = $state(null);

  // --- Upload State for Display/Next Steps ---
  let postUrl: string | null = $state(null);
  let postFields: Record<string, string> | null = $state(null);
  let jobId: string | null = $state(null);
  let s3Key: string | null = $state(null);

  // --- S3 UPLOAD LOGIC ---

  /**
   * Handles the entire 3-step upload process on button click:
   * 1. Get Presigned POST URL and Fields from Backend (FastAPI)
   * 2. HTTP POST file directly to S3
   * 3. Register job with SvelteKit server action
   */
  async function handleFullUpload() {
    if (!files || files.length === 0) {
        errorMessage = "Please select a file first.";
        return;
    }

    // Safely extract the first file
    const file = Array.from(files)[0];

    // Reset state and set initial status
    errorMessage = null;
    uploadStatus = 'fetching-url';
    uploadMessage = `1/3: Requesting secure S3 credentials for ${file.name}...`;
    logger.info("Starting upload process.", { filename: file.name });

    // --- STEP 1: Get Presigned POST Data from Backend (FastAPI) ---
    const endpoint = '/api/upload'; // SvelteKit Proxy URL
    try {
        const urlResponse = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ "filename": file.name })
        });

        if (!urlResponse.ok) {
            const errorData = await urlResponse.json();
            const detailMessage = errorData.detail?.[0]?.msg || errorData.error || JSON.stringify(errorData);
            errorMessage = `Credential Fetch Failed: ${urlResponse.status}. Detail: ${detailMessage.substring(0, 150)}`;
            logger.error({ status: urlResponse.status, body: errorData }, errorMessage);
            uploadStatus = 'error';
            return;
        }

        const data = await urlResponse.json();

        postUrl = data.postUrl;
        postFields = data.fields;
        jobId = data.jobId;
        s3Key = data.s3Key;

        if (!postUrl || !postFields || !jobId) {
            errorMessage = "Backend response missing required POST data (URL/Fields/Job ID).";
            uploadStatus = 'error';
            return;
        }

        logger.debug("Received POST credentials.", { jobId });

        // --- STEP 2: Upload the File Directly to S3 using HTTP POST ---
        uploadStatus = 'uploading';
        uploadMessage = `2/3: Uploading ${file.name} directly to S3...`;

        // 1. Construct the FormData object
        const formData = new FormData();

        // 2. Append all required S3 security fields first
        Object.entries(postFields).forEach(([key, value]) => {
            formData.append(key, value);
        });

        // 3. Append the actual file, S3 expects the file field to be named 'file'
        formData.append('file', file);

        // 4. Execute the POST upload
        const s3Response = await fetch(postUrl, {
            method: 'POST',
            // CRITICAL: Do NOT set Content-Type header with FormData. Browser handles it.
            body: formData
        });

        if (s3Response.status === 201) { // 201 Created is the success status we signed for
            // --- UPLOAD SUCCESS ---
            uploadMessage = `S3 upload complete. Registering job...`;

            // --- STEP 3: Trigger Server Action (registerJob) ---
            const registerFormData = new FormData();
            registerFormData.append('jobId', jobId);
            registerFormData.append('s3Key', s3Key);
            registerFormData.append('title', file.name);

            const registerResponse = await fetch('?/registerJob', {
                method: 'POST',
                body: registerFormData,
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

        } else {
            // --- UPLOAD FAILURE ---
            const s3ErrorText = await s3Response.text();
            // Attempt to extract the error message from the XML response
            const detailedError = s3ErrorText.match(/<Message>(.*?)<\/Message>/)?.[1] || s3ErrorText;

            uploadStatus = 'error';
            errorMessage = `S3 POST failed (Status: ${s3Response.status}). Detail: ${detailedError.substring(0, 150)}`;
            logger.error("S3 POST Failed.", { status: s3Response.status, statusText: s3Response.statusText, responseBody: s3ErrorText });
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
                    disabled={!files || files.length === 0 || uploadStatus === 'uploading' || uploadStatus === 'fetching-url' || uploadStatus === 'error'}
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
