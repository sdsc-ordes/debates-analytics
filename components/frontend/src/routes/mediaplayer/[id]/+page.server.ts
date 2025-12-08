import type { PageServerLoad } from "./$types";
import { client } from '$lib/api/client';
import { error } from "@sveltejs/kit";
import { logger } from "$lib/utils/logger";
import type { components } from '$lib/api/schema';

type MetadataResponse = components['schemas']['MetadataResponse'];

export const load: PageServerLoad = async ({ params, fetch }) => {
  try {
    // 1. Rename first error to 'metadataError'
    const { data, error: metadataError } = await client.GET("/db/get-metadata", {
      params: {
        query: {
          media_id: params.id,
        }
      },
      fetch: fetch
    });

    if (metadataError || !data) {
      logger.error(metadataError, "API Error:");
      throw error(404, "Media not found");
    }

    const metadata = data?.metadata;
    logger.info(metadata, "Metadata received");

    //const mediaKey = metadata.s3_key;
    //const objectKey = metadata.transcript_s3_keys;

    // 2. Rename second error to 'signedUrlsError'
    const { data: signedUrlsData, error: signedUrlsError } = await client.GET("/db/get-signed-urls", {
      params: {
        query: {
          media_id: params.id,
        }
      },
      fetch: fetch
    });

    if (signedUrlsError) {
        logger.error(signedUrlsError, "Signed URL Error:");
        // Handle this error appropriately, maybe you still return metadata but without URLs?
    }

    return {
      metadata: metadata,
      signedUrls: signedUrlsData // Don't forget to return this if you need it!
    };

  } catch (err) {
    if (err?.status) throw err;

    console.error(err, "Load Error");
    throw error(500, "Internal Server Error");
  }
};