import { sequence } from "@sveltejs/kit/hooks"
import { redirect, type Handle, type HandleFetch } from "@sveltejs/kit"
import { logger } from "$lib/utils/logger"

// --- CONFIGURATION ---
const EDITOR_ROUTES = ["/dashboard", "/upload"]

/**
 * 1. LOGGING HANDLE (Your existing logic)
 * This runs first to measure the total time of the request.
 */
const loggingHandle: Handle = async ({ event, resolve }) => {
  const start = performance.now()
  const { method, url } = event.request

  const requestLogger = logger.child({
    type: "incoming",
    method,
    path: url,
  })

  const response = await resolve(event)

  const durationMs = (performance.now() - start).toFixed(2)

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
 * 2. AUTH HANDLE: Identify the user
 * This checks WHO the user is (e.g. by reading a cookie or proxy header).
 */
const authHandle: Handle = async ({ event, resolve }) => {
  // TODO: Adapt this to how your Proxy/Login sets the session.
  // Example: Your proxy might set a cookie named 'session_id' or 'role'
  const sessionCookie = event.cookies.get("session_id")

  // Placeholder logic:
  // You need to set event.locals.user based on your actual auth method.
  if (sessionCookie) {
    // If you have a JWT, verify it here.
    // If you use a simple secret for the editor:
    const role = sessionCookie === "editor-secret" ? "editor" : "reader"

    event.locals.user = { id: "user-123", role }
  } else {
    event.locals.user = null
  }

  return resolve(event)
}

/**
 * 3. GUARD HANDLE: Protect the routes
 * This checks permissions and REDIRECTS if necessary.
 */
const guardHandle: Handle = async ({ event, resolve }) => {
  const url = event.url.pathname

  // Check if current path starts with any of the protected routes
  const isProtected = EDITOR_ROUTES.some((route) => url.startsWith(route))

  if (isProtected) {
    const user = event.locals.user

    // Case A: Not logged in at all
    if (!user) {
      // Redirect to your login route (or the proxy entry point)
      // We use 'returnTo' so we can send them back after login
      throw redirect(303, `/edit?returnTo=${url}`)
    }

    // Case B: Logged in, but wrong role
    if (user.role !== "editor") {
      logger.warn(`Unauthorized access to ${url} by user role: ${user.role}`)
      // Redirect to home or show a 403 error page
      throw redirect(303, "/")
    }
  }

  return resolve(event)
}

// --- EXPORTS ---

// Execute these handles in order: Log -> Auth -> Guard -> Page
export const handle = sequence(loggingHandle, authHandle, guardHandle)

/**
 * OUTGOING REQUESTS (Unchanged)
 */
export const handleFetch: HandleFetch = async ({ request, fetch }) => {
  const start = performance.now()
  const url = request.url
  const isBackendCall = url.includes("backend") || url.includes("8000")

  if (isBackendCall) {
    logger.info(
      { type: "outgoing", target: url, method: request.method },
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
