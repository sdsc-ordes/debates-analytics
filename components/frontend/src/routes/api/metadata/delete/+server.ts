import { json } from "@sveltejs/kit"
import { BackendUrl } from "$lib/config"
import { logger } from "$lib/utils/logger"
import type { RequestHandler } from "./$types"

export const POST: RequestHandler = async ({ request }) => {
  logger.info("Received POST request for /api/delete.")

  try {
    const bodyObject = await request.json()
    const mediaId = bodyObject.mediaId

    if (!mediaId || typeof mediaId !== "string") {
      logger.warn(
        { body: bodyObject },
        "Request body invalid or missing filename.",
      )
      return json(
        { error: "Invalid request body: mediaId is required." },
        { status: 400 },
      )
    }

    const backendApiUrl = `${BackendUrl}/admin/delete`
    logger.info(`Delete ${backendApiUrl} for mediaId: ${mediaId}`)

    const backendResponse = await fetch(backendApiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ mediaId }),
    })

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text()
      throw new Error(
        `External backend failed: ${backendResponse.status} ${backendResponse.statusText} - ${errorText}`,
      )
    }

    return backendResponse
  } catch (error) {
    const err = error as Error
    logger.error(`API Error: ${err.message}`, { error: err })

    return json(
      {
        error: "Failed to communicate with the backend service.",
        detail: err.message,
      },
      { status: 500 },
    )
  }
}
