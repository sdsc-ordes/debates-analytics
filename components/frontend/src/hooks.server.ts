import type { Handle, HandleFetch } from "@sveltejs/kit"
import { logger } from "$lib/utils/logger"

/**
 * 1. INCOMING REQUESTS (Browser -> SvelteKit)
 */
export const handle: Handle = async ({ event, resolve }) => {
  const start = performance.now()
  const { method, url } = event.request

  // Create a child logger with request context (request ID is great here if you have one)
  const requestLogger = logger.child({
    type: "incoming",
    method,
    path: url,
  })

  // Process the request
  const response = await resolve(event)

  const durationMs = (performance.now() - start).toFixed(2)

  // Log the outcome
  // Pino format: logger.info(obj, msg)
  requestLogger.info(
    {
      status: response.status,
      duration: durationMs,
    },
    `${method} ${url}`,
  )

  return response
}

/**
 * 2. OUTGOING REQUESTS (SvelteKit -> Python Backend)
 */
export const handleFetch: HandleFetch = async ({ request, fetch }) => {
  const start = performance.now()
  const url = request.url

  // Filter to only log backend calls (reduce noise)
  const isBackendCall = url.includes("backend") || url.includes("8000")

  if (isBackendCall) {
    // We don't use child loggers here as easily, so we just log directly
    logger.info(
      {
        type: "outgoing",
        target: url,
        method: request.method,
      },
      `Fetching backend: ${url}`,
    )
  }

  const response = await fetch(request)

  if (isBackendCall) {
    const durationMs = (performance.now() - start).toFixed(2)

    logger.info(
      {
        type: "outgoing_response",
        target: url,
        status: response.status,
        duration: durationMs,
      },
      `Backend replied: ${response.status}`,
    )
  }

  return response
}
