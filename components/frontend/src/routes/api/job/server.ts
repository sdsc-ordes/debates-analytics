import { json } from "@sveltejs/kit";
import { fetchUploadUrl } from "$lib/server/fetchUploadUrl";
import { logger } from '$lib/utils/logger';
import type { RequestHandler } from "./$types"; // Added type import

export const POST: RequestHandler = async ({ request }) => {
  logger.info("Received POST request for /api/upload proxy.");

  try {
    // 1. Safely read body and extract filename
    const bodyObject = await request.json();
    const filename = bodyObject.filename;

    if (!filename || typeof filename !== 'string') {
        logger.warn("Request body invalid or missing filename.", { body: bodyObject });
        return json({ error: "Invalid request body: filename is required." }, { status: 400 });
    }

    logger.info({filename: filename}, "filename in api");

    // 2. Call the utility function to get the credentials from FastAPI
    const credentials = await fetchUploadUrl(filename);

    logger.info("Successfully fetched S3 POST credentials.", { jobId: credentials.jobId });

    // 3. FIX: Return the credentials object directly using SvelteKit's json() helper.
    // This allows the frontend to easily access data.postUrl, data.fields, etc.
    return json(credentials, { status: 200 });

  } catch (error) {
    const err = error as Error;
    logger.error(`API Error: ${err.message}`, { error: err });

    // When returning an error from the server endpoint, use json() with the appropriate status code
    return json({
        error: "Failed to communicate with the backend service.",
        detail: err.message
    }, { status: 500 });
  }
};
