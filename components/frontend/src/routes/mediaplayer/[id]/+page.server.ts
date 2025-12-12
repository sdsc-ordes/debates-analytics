import type { PageServerLoad } from "./$types";
import { client } from "$lib/api/client";
import { error } from "@sveltejs/kit";
import { logger } from "$lib/utils/logger";

export const load: PageServerLoad = async ({ params, fetch }) => {
  const mediaId = params.id;

  try {
    const [metadataResponse, signedUrlsResponse] = await Promise.all([
      client.GET("/db/get-metadata", {
        params: { query: { media_id: mediaId } },
        fetch,
      }),
      client.GET("/db/get-signed-urls", {
        params: { query: { media_id: mediaId } },
        fetch,
      }),
    ]);

    const { data: metadata, error: metadataError } = metadataResponse;

    if (metadataError || !metadata) {
      logger.error(metadataError, "Metadata API Error:");
      throw error(404, "Media metadata not found");
    }

    const { data: signedUrls, error: signedUrlsError } = signedUrlsResponse;

    if (signedUrlsError) {
      logger.error(signedUrlsError, "Signed URL Error:");
    }

    return {
      mediaId: mediaId,
      metadata: metadata,
      signedUrls: signedUrls || null,
    };
  } catch (err) {
    if (err?.status) throw err;

    console.error(err, "Load Error");
    throw error(500, "Internal Server Error");
  }
};
