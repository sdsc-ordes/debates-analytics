import { json } from "@sveltejs/kit";
import { BackendUrl } from "$lib/config";
import { logger } from '$lib/utils/logger';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ request }) => {
  logger.info("Received POST request for /api/upload.");

  try {
    const bodyObject = await request.json();
    const filename = bodyObject.filename;

    if (!filename || typeof filename !== 'string') {
        logger.warn({ body: bodyObject }, "Request body invalid or missing filename.");
        return json({ error: "Invalid request body: filename is required." }, { status: 400 });
    }

    const backendApiUrl = `${BackendUrl}/get-presigned-post`;
    logger.info(`Fetching S3 POST credentials from ${backendApiUrl} for filename: ${filename}`);

    const backendResponse = await fetch(backendApiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ filename }),
    });

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text();
      throw new Error(`External backend failed: ${backendResponse.status} ${backendResponse.statusText} - ${errorText}`);
    }

    const credentials = await backendResponse.json();

    logger.info({ media_id: credentials.jobId }, "Successfully fetched S3 POST credentials.");

    return json(credentials);

  } catch (error) {
    const err = error as Error;
    logger.error(`API Error: ${err.message}`, { error: err });

    return json({
        error: "Failed to communicate with the backend service.",
        detail: err.message
    }, { status: 500 });
  }
};
