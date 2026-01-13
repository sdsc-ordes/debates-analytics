import type { LayoutServerLoad } from "./$types"

export const load: LayoutServerLoad = async ({ locals }) => {
  // Pass the user object (set in hooks.server.ts) to the frontend
  return {
    user: locals.user,
  }
}
