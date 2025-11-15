import type { PageServerLoad, Actions } from "./$types"
import { error, fail } from "@sveltejs/kit"
import { fetchUploadedVideos } from "$lib/server/fetchUploadedVideos" // Assume this fetches the list of existing videos
//import { processUpload } from "$lib/server/processUpload" // Assume this handles the video file and metadata

// Define the interface for a video/job entry to be returned by the load function
interface UploadedVideo {
    id: string;
    title: string;
    status: 'pending' | 'processing' | 'ready';
    uploadDate: string;
}

// --- LOAD FUNCTION ---
// Fetches the list of already uploaded videos (similar to a "job list")
export const load: PageServerLoad = async ({ locals }) => {
    try {
        // Assume locals contains user information for authentication/scoping
        // If the user isn't authenticated, you might redirect them or throw a 401 error.

        const response: UploadedVideo[] = await fetchUploadedVideos()

        return {
            // Data returned to the +page.svelte component
            mediaList: response.uploadedMedia,
        }
    } catch (err) {
        // Log the error and fail gracefully
        console.error("Error fetching uploaded videos list:", err)
        throw error(500, "Failed to load uploaded video list.")
    }
}

/*
// --- ACTIONS ---
// Handles the form submission (the file upload and associated metadata)
export const actions: Actions = {
    // The default action handles the primary file upload
    default: async ({ request }) => {
        try {
            // 1. Get the form data from the request
            const data = await request.formData()

            // 2. Extract the file and any metadata
            const videoFile = data.get('video') as File | null
            const title = data.get('title') as string

            // 3. Simple validation (client-side validation is usually better)
            if (!videoFile || videoFile.size === 0) {
                return fail(400, { success: false, message: "Please select a video file to upload." })
            }
            if (!title) {
                 return fail(400, { success: false, message: "Please provide a title for the video." })
            }

            // 4. Process the upload using your backend utility
            const newJobId: string = await processUpload(videoFile, title)

            // 5. Return a success response
            return {
                success: true,
                message: `Video "${title}" submitted for processing. Job ID: ${newJobId}`,
                jobId: newJobId
            }

        } catch (err) {
            // Log the error and return a failure response
            console.error("Error processing video upload:", err)

            // Return a fail response to be handled by the client-side form action.
            return fail(500, {
                success: false,
                message: "Upload failed due to a server error."
            })
        }
    }
}
*/