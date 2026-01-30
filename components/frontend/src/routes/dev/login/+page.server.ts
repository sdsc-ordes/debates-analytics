import { redirect } from "@sveltejs/kit"
import type { Actions } from "./$types"
import { dev } from "$app/environment";

export const actions: Actions = {
  // This handles the POST to /dev/login?/logout
  logout: async ({ cookies }) => {
    // Delete the session cookie
    cookies.delete("session_id", { path: "/" })

    // Redirect to the home page
    throw redirect(303, "/")
  },

  // Include these if you want the "Login as Editor" buttons to work too
  loginEditor: async ({ cookies }) => {
    cookies.set("session_id", "editor-secret", {
      path: "/",
      httpOnly: true,
      sameSite: 'lax',
      secure: !dev,
      maxAge: 60 * 60 * 24,
    })
    throw redirect(303, "/dashboard")
  },

  loginReader: async ({ cookies }) => {
    cookies.set("session_id", "reader-token", {
      path: "/",
      httpOnly: true,
      sameSite: 'lax',
      secure: !dev,
      maxAge: 60 * 60 * 24,
    })
    throw redirect(303, "/")
  },
}
