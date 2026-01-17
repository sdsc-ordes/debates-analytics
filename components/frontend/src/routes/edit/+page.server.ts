import { redirect } from "@sveltejs/kit"
import type { PageServerLoad } from "./$types"

export const load: PageServerLoad = async ({ cookies, url }) => {
  // Set the cookie that your hooks.server.ts expects.
  // Since the user reached this code, they passed the Proxy Auth.
  cookies.set("session_id", "editor-secret", {
    path: "/",
    httpOnly: true,
    // Uncomment this in production (HTTPS)
    // secure: true,
    maxAge: 60 * 60 * 24, // 1 day
  })

  // Redirect to the home page
  const returnTo = url.searchParams.get("returnTo") || "/dashboard"
  throw redirect(303, returnTo)
}
