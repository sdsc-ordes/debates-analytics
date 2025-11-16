import type { SignedUploadUrl } from "$lib/interfaces/metadata.interface"
import { BackendUrl } from "$lib/config"

export async function fetchUploadUrl(
  filename: string,
): Promise<SignedUploadUrl> {
  try {
    // FastAPI endpoint to retrieve signed URLs
    const apiUrl = `${BackendUrl}/get-presigned-post`

    // Request payload for signed URLs
    const payload = JSON.stringify({
      filename: filename,
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
      throw new Error(`Error fetching signed upload URL: ${response.statusText}`)
    }

    // Extract JSON from the response
    const data = await response.json()
    console.log(data);
    const signeUploadUrl = data
    return signeUploadUrl
  } catch (error) {
    console.error("Error in fetchUploadUrl:", error)
    throw error
  }
}
