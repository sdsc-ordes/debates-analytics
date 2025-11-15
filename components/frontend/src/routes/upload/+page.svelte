<script lang="ts">
    import { FileIcon } from 'lucide-svelte';
    import { FileUpload } from '@skeletonlabs/skeleton-svelte';

    // --- Upload State ---
    // This state variable will be bound to the FileUpload component to capture accepted files.
    let acceptedFiles: File[] = $state([]);
    let uploadStatus: 'idle' | 'in-progress' | 'success' | 'error' = $state('idle');
    let uploadMessage: string = $state('');

    // --- S3 UPLOAD LOGIC ---
    async function handleUpload() {
        console.log("button for upload clicked")
        if (acceptedFiles.length === 0) {
            uploadStatus = 'error';
            uploadMessage = 'Please select a file first.';
            return;
        }

        uploadStatus = 'in-progress';
        uploadMessage = 'Starting upload process...';

        const file = acceptedFiles[0];
        console.log(file);

        // 1. Get the Presigned Upload URL from the Backend
        uploadMessage = `Requesting S3 URL for job ID: ${file.name}`;

        const requestBody = JSON.stringify({
            filename: file.name
        });

        const urlResponse = await fetch('http://backend:8000/get-upload-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: requestBody
        });

        if (!urlResponse.ok) {
            uploadStatus = 'error';
            uploadMessage = `Failed to get upload URL from backend (${urlResponse.status})`;
            console.error(uploadMessage);
            return;
        }

        const { uploadUrl, s3Key } = await urlResponse.json();

        if (!uploadUrl) {
            uploadStatus = 'error';
            uploadMessage = 'Backend returned no upload URL.';
            return;
        }

        // 2. Upload the File Directly to S3 using HTTP PUT
        uploadMessage = `Uploading file to S3: ${file.name}`;

        try {
            const s3Response = await fetch(uploadUrl, {
                method: 'PUT',
                // Important: S3 upload requires the Content-Type header to match the file type
                headers: { 'Content-Type': file.type },
                body: file
            });

            if (s3Response.ok) {
                uploadStatus = 'success';
                uploadMessage = `File uploaded successfully! Job ID: ${jobId}`;
                // Optionally: Trigger the analysis workflow via another backend call here
                // triggerAnalysis(jobId, s3Key);

                // Clear files after successful upload
                acceptedFiles = [];
            } else {
                uploadStatus = 'error';
                uploadMessage = `S3 upload failed. Status: ${s3Response.status}`;
                console.error('S3 Upload Error:', s3Response.statusText);
            }
        } catch (e) {
            uploadStatus = 'error';
            uploadMessage = `Network error during S3 upload. Check console.`;
            console.error('Upload network error:', e);
        }
    }

    async function prepareUpload(files: File[]) {
        console.log("received file of length", files.length)
    }
</script>

<svelte:head>
    <title>Upload</title>
    <meta name="description" content="File upload" />
</svelte:head>

<section>
    <div class="info">

        <div class="links">
            <a href="YOUR_GITHUB_LINK_HERE" aria-label="GitHub Repository Link">
                <FileIcon class="size-6 text-[var(--primary-dark-color)]" />
            </a>
        </div>

        <h1>Video Upload</h1>

        <div class="w-full space-y-4">
            <!-- File Upload Section -->

            <FileUpload onFileAccept={prepareUpload}>
                <FileUpload.Label>Upload your files</FileUpload.Label>
                <FileUpload.Dropzone>
                    <FileIcon class="size-10" />
                    <span>Select file or drag here.</span>
                    <FileUpload.Trigger class="button-primary">Browse Files</FileUpload.Trigger>
                    <FileUpload.HiddenInput />
                </FileUpload.Dropzone>
                <FileUpload.ItemGroup>
                    <FileUpload.Context>
                        {#snippet children(fileUpload)}
                            {#each fileUpload().acceptedFiles as file (file.name)}
                                <FileUpload.Item {file}>
                                    <FileUpload.ItemName>{file.name}</FileUpload.ItemName>
                                    <FileUpload.ItemSizeText>{file.size} bytes</FileUpload.ItemSizeText>
                                    <FileUpload.ItemDeleteTrigger />
                                </FileUpload.Item>
                            {/each}
                        {/snippet}
                    </FileUpload.Context>
                </FileUpload.ItemGroup>
            </FileUpload>

            <!-- Status and Submit Button -->
            <div class="flex flex-col items-start gap-2">
                <!-- Status Message -->
                {#if uploadStatus !== 'idle'}
                    <p class="p-2 rounded-lg text-sm"
                        class:bg-warning-500={uploadStatus === 'in-progress'}
                        class:bg-success-500={uploadStatus === 'success'}
                        class:bg-error-500={uploadStatus === 'error'}
                        class:text-white={uploadStatus !== 'idle'}
                    >
                        {uploadMessage}
                    </p>
                {/if}

                <!-- Submit Button -->
                <button
                    type="button"
                    class="btn variant-filled-primary button-primary"
                    onclick={handleUpload}
                >
                    {#if uploadStatus === 'in-progress'}
                        Uploading...
                    {:else}
                        Upload Video
                    {/if}
                </button>
            </div>

        </div>
    </div>
</section>

<style>
    /* Styling copied from the previous exchange to match the page theme */
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
</style>
