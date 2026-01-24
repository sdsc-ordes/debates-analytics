import { env } from "$env/dynamic/private"
import type { RequestHandler } from "./$types"
import { logger } from "$lib/utils/logger"
import { BackendUrl } from "$lib/config"

const BACKEND_URL = BackendUrl

const proxy: RequestHandler = async ({ request, params, url }) => {
  const path = params.path
  const targetUrl = `${BACKEND_URL}/${path}${url.search}`

  logger.info(`[Proxy] ${request.method} ${url.pathname} -> ${targetUrl}`)

  try {
    const response = await fetch(targetUrl, {
      method: request.method,
      headers: request.headers,
      body: request.body,
      // @ts-ignore - Required for Node 18+ streaming
      duplex: "half",
    })

    return response
  } catch (err) {
    logger.error("[Proxy Error]", err)
    return new Response(JSON.stringify({ error: "Backend unreachable" }), {
      status: 502,
      headers: { "Content-Type": "application/json" },
    })
  }
}

// Export handlers for EVERY method
export const GET = proxy
export const POST = proxy
export const PUT = proxy
export const DELETE = proxy
export const PATCH = proxy
