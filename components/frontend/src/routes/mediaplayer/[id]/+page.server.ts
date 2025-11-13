import type { PageServerLoad } from "./$types"
import type {
  SignedUrls,
  ResponseMetadata,
} from "$lib/interfaces/metadata.interface"
import { fetchMedia } from "$lib/server/fetchMedia"
import { fetchMetadata } from "$lib/server/fetchMetadata"
import { error } from "@sveltejs/kit" // Import the error function

export const load: PageServerLoad = async ({ params }) => {
  try {
    const job_id: string = params.id

    // Fetch metadata FIRST.  If it fails, it's a 404.
    const metadata: ResponseMetadata = await fetchMetadata(job_id) // Await here
    console.log(metadata)

    // Check if metadata exists. If not, it's a 404
    if (
      !metadata
    ) {
      throw error(404, "Not Found") // Throw 404 if metadata is missing or incomplete
    }

    const signedUrls: SignedUrls = await fetchMedia(job_id)

    return {
      job_id: job_id,
      debate: metadata.debate,
      speakers: metadata.speakers.speakers,
      segments: metadata.segments.segments,
      subtitles: metadata.subtitles.subtitles,
      subtitles_en: metadata.subtitles_en.subtitles,
      signedUrls: signedUrls,
    }
  } catch (err) {
    // Check if the error is already a 404. If so, re-throw it.
    if (err.status === 404) {
      throw err
    }

    // Log the error for debugging purposes
    console.error("Error loading collections:", err)

    // For other errors (not 404), throw a 500 error.
    throw error(500, "Internal Server Error")
  }
}
