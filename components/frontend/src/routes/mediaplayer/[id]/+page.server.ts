import type { PageServerLoad } from "./$types";
import type { SignedUrls, ResponseMetadata } from "$lib/interfaces/metadata.interface";
import { fetchMedia } from "$lib/server/fetchMedia";
import { fetchMetadata } from "$lib/server/fetchMetadata";
import { error } from '@sveltejs/kit'; // Import the error function

export const load: PageServerLoad = async ({ params }) => {
    try {
        const s3Prefix: string = params.id;

        // Fetch metadata FIRST.  If it fails, it's a 404.
        const metadata: ResponseMetadata = await fetchMetadata(s3Prefix); // Await here

        // Check if metadata exists. If not, it's a 404
        if (!metadata || !metadata.debate || !metadata.debate.s3_keys || !metadata.debate.media) {
            throw error(404, 'Not Found'); // Throw 404 if metadata is missing or incomplete
        }

        const objectKeys: string[] = metadata.debate.s3_keys.map(item => item.name);
        const mediaKey = metadata.debate.media.key;
        const signedUrls: SignedUrls = await fetchMedia(
            s3Prefix,
            objectKeys,
            mediaKey,
        );

        return {
            prefix: s3Prefix,
            media: metadata.debate.media,
            debate: metadata.debate,
            speakers: metadata.speakers.speakers,
            segments: metadata.segments.segments,
            subtitles: metadata.subtitles.subtitles,
            subtitles_en: metadata.subtitles_en.subtitles,
            signedUrls: signedUrls,
        };
    } catch (err) {
        // Check if the error is already a 404. If so, re-throw it.
        if (err.status === 404) {
            throw err;
        }

        // Log the error for debugging purposes
        console.error("Error loading collections:", err);

        // For other errors (not 404), throw a 500 error.
        throw error(500, 'Internal Server Error');
    }
};
