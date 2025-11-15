import type { UploadedVideosResponse } from "$lib/interfaces/uploaded.interface"
import { BackendUrl } from "$lib/config"

export async function fetchUploadedVideos(
): Promise<UploadedVideosResponse> {
  try {
    // FastAPI endpoint to retrieve signed URLs
    const apiUrl = `${BackendUrl}/get-uploaded`

    console.log(`API call to ${apiUrl}`)

    // Fetch signed URL from FastAPI backend
    const response = await fetch(apiUrl, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })
    if (!response.ok) {
      throw new Error(`Error fetching jobs: ${response.statusText}`)
    }

    // Extract JSON from the response
    const data = await response.json()
    console.log(data);
    return data
  } catch (error) {
    console.error("Error in fetchMedia:", error)
    throw error
  }
}
