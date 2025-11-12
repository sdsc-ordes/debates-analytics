import type { DebateMetadata } from "$lib/interfaces/metadata.interface"
import { BackendUrl } from "$lib/config"

export async function fetchMetadata(job_id: String): DebateMetadata {
  try {
    // FastAPI endpoint to fetch metadata
    const apiUrl = `${BackendUrl}/get-metadata`

    // Request payload for fetching metadata
    const payload = JSON.stringify({ job_id: job_id, expiration: 3600 })
    console.log(`API call to ${apiUrl} with paylosd: ${payload}`)

    // Fetch metadata from FastAPI backend
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: payload,
    })

    if (!response.ok) {
      throw new Error(`Error fetching metadata: ${response.statusText}`)
    }

    // Extract JSON from the response
    const data = await response.json()
    console.log(data);
    const metaData = data
    return metaData
  } catch (error) {
    console.error("Error in fetchMetadata:", error)
    throw error
  }
}
