import { fail } from "@sveltejs/kit"
import type { PageServerLoad, Actions } from "./$types"
import { client } from "$lib/api/client"
import { logger } from "$lib/utils/logger"
import type { components } from "$lib/api/schema"
type MediaListItem = components["schemas"]["MediaListItem"]

export const load: PageServerLoad = async ({ fetch }) => {
  const { data, error } = await client.GET("/admin/list", {
    fetch: fetch,
  })

  if (error || !data) {
    console.error("Load Error:", error)
    return {
      items: [],
      error: (error as any)?.detail || "System Unavailable: Unable to fetch media list."
    }
  }

  const sortedItems = (data.items || []).sort(
    (a: MediaListItem, b: MediaListItem) =>
      new Date(b.created_at ?? 0).getTime() -
      new Date(a.created_at ?? 0).getTime(),
  )

  return {
    items: sortedItems,
  }
}

export const actions: Actions = {
  delete: async ({ request, fetch }) => {
    logger.info("IN DELETE")
    const formData = await request.formData()
    const mediaId = formData.get("mediaId") as string

    if (!mediaId) return fail(400, { missing: true })

    const { error } = await client.POST("/admin/delete", {
      body: { mediaId: mediaId },
      fetch: fetch,
    })

    if (error) {
      return fail(500, { error: "Delete failed on server" })
    }

    return { success: true }
  },
  reindex: async ({ request, fetch }) => {
    logger.info("IN REINDEX")
    const formData = await request.formData()
    const mediaId = formData.get("mediaId") as string

    if (!mediaId) return fail(400, { missing: true })

    const { error } = await client.POST("/admin/reindex", {
      body: { mediaId: mediaId },
      fetch: fetch,
    })

    if (error) {
      return fail(500, { error: "Reindex failed on server" })
    }

    return { success: true }
  },
}
