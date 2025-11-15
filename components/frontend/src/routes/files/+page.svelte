<script lang="ts">
  import { logger } from '$lib/utils/logger'
	let files = $state();

	$effect(() => {
		if (files) {
			// Note that `files` is of type `FileList`, not an Array:
			// https://developer.mozilla.org/en-US/docs/Web/API/FileList
      console.log("running in effect")
			console.log(files);
      logger.info({file: files}, "file for upload");

			for (const file of files) {
				console.log(`in effect: ${file.name}: ${file.size} bytes`);
        const uploadUrl = getUploadUrl(file.name);
        console.log("uploadUrl", uploadUrl);
        logger.info({uploadUrl: uploadUrl}, "received and upload url");
			}

		}
	});

  let errorMessage: string | null = null;

  async function getUploadUrl(filename: string) {
    logger.info({filename: filename}, "received in getUploadUrl")
    console.log(filename, "filename received in getUploadUrl")
    errorMessage = null;
    try {
      const response = await fetch('/api/upload', {  // Call the API endpoint
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({"filename": filename}) // Send the solrQuery in the body
      });
      if (!response.ok) {
        const errorData = await response.json(); // Try to get error details
        errorMessage = errorData.error || `Search failed: ${response.status} ${response.statusText}`; // Display detailed error
        console.error(errorMessage);
        return; // Stop processing if the request failed
      }
      const data = await response.json();
      console.log(data);
    } catch (error) {
      errorMessage = `An unexpected error occurred: ${error.message}`;
      console.error(errorMessage);
    }
  }
</script>

<label for="avatar">Upload a media file</label>
<input accept="image/png, image/jpeg" bind:files id="avatar" name="avatar" type="file" />

<label for="many">Upload multiple files of any type:</label>
<input bind:files id="many" multiple type="file" />

{#if files}
	<h2>Selected files:</h2>
	{#each Array.from(files) as file}
		<p>{file.name} ({file.size} bytes)</p>
	{/each}
{/if}
