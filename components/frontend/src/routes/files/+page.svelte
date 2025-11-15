<script lang="ts">
  import { logger } from '$lib/utils/logger';
  // The files variable is bound to the input's FileList
  let files: FileList | undefined = $state();

  let errorMessage: string | null = $state(null);

  // State to hold the final presigned URLs for display/next steps
  let uploadedUrls: { filename: string, uploadUrl: string }[] = $state([]);

  /**
   * Effect runs whenever files is set (i.e., when a user selects files).
   * This handles all the asynchronous fetching logic.
   */
  $effect(async () => {
    // Only run if files is present and there's at least one file
    if (files && files.length > 0) {
      logger.info({ fileCount: files.length }, "Files accepted in effect, starting URL fetch.");
      errorMessage = null;
      uploadedUrls = [];

      const fileArray = Array.from(files);

      for (const file of fileArray) {
        // --- NEW CHECK HERE ---
        if (!file || !file.name) {
            logger.warn("Skipping file: File object or filename is invalid.");
            continue; // Skip this iteration if data is bad
        }
        // ----------------------

        logger.info({ filename: file.name, size: file.size }, "Processing file for upload URL.");

        const urlResult = await getUploadUrl(file.name);

        if (urlResult) {
          // If successful, save the data
          uploadedUrls.push({
            filename: file.name,
            uploadUrl: urlResult
          });
          logger.info({ uploadUrl: urlResult }, `Successfully received upload URL for ${file.name}`);
        } else {
          // If the function failed, it already set the errorMessage. Stop here.
          break;
        }
      }
    }
  });

  /**
   * Calls the backend API to retrieve a presigned upload URL for a given filename.
   * @param filename - The name of the file to upload.
   * @returns The presigned upload URL string or null if failed.
   */
  async function getUploadUrl(filename: string): Promise<string | null> {
    logger.info({ filename: filename }, "Received filename to request upload URL.");

    // Using '/get-upload-url' which is typically handled by SvelteKit's endpoint or proxy.
    const endpoint = '/api/upload';

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        // Request body structure remains correct: { "filename": "actual_name.mp4" }
        body: JSON.stringify({ "filename": filename })
      });

      if (!response.ok) {
        // Log detailed error from the backend
        const errorData = await response.json();
        // Capture the detail message from FastAPI's 422 error body
        const detailMessage = errorData.detail?.[0]?.msg || JSON.stringify(errorData);

        errorMessage = `Upload URL request failed: ${response.status}. Detail: ${detailMessage}`;
        logger.error({ status: response.status, body: errorData }, errorMessage);
        return null;
      }

      const data = await response.json();
      logger.debug({ response: data }, "API responded with URL data.");

      // Assuming your backend returns { uploadUrl: string, ... }
      return data.uploadUrl || null;

    } catch (error) {
      errorMessage = `An unexpected network error occurred: ${error}`;
      logger.error({ error: error }, errorMessage);
      return null;
    }
  }
</script>

<label for="many">Upload multiple files of any type:</label>
<input bind:files id="many" multiple type="file" />

{#if errorMessage}
    <p class="text-red-500 font-bold">{errorMessage}</p>
{/if}

{#if files && files.length > 0}
  <h2>Selected files:</h2>
  <!-- FIX 3: Iterate over Array.from(files) for reliable iteration -->
  {#each Array.from(files) as file}
    <p>{file.name} ({file.size} bytes)</p>
  {/each}
{/if}

{#if uploadedUrls.length > 0}
    <h2>Fetched Upload URLs:</h2>
    {#each uploadedUrls as item}
        <p class="text-green-600">✅ {item.filename}: <code class="bg-gray-100 p-1 text-xs">{item.uploadUrl.substring(0, 50)}...</code></p>
    {/each}
{/if}
