import type { SignedUrls } from "$lib/interfaces/metadata.interface"
import { BackendUrl } from "$lib/config"

export async function fetchMedia(
  job_id: string,
): Promise<SignedUrls> {
  try {
    // FastAPI endpoint to retrieve signed URLs
    const apiUrl = `${BackendUrl}/get-signed-urls`

    // Request payload for signed URLs
    const payload = JSON.stringify({
      job_id: job_id,
    })
    console.log(`API call to ${apiUrl} with paylosd: ${payload}`)

    // Fetch signed URL from FastAPI backend
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: payload,
    })
    if (!response.ok) {
      throw new Error(`Error fetching signed URL: ${response.statusText}`)
    }

    // Extract JSON from the response
    const data = await response.json()
    console.log(data);
    const signedUrls = data
    return signedUrls
  } catch (error) {
    console.error("Error in fetchMedia:", error)
    throw error
  }
}
