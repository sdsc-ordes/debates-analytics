import { json } from "@sveltejs/kit"
import { BackendUrl } from "$lib/config"

export async function POST({ request, fetch }) {
  const { s3Key, mediaId, title } = await request.json()
  console.log(
    `Sending processing request for S3 key: ${s3Key}, media ID: ${mediaId}`,
  )

  const response = await fetch(`${BackendUrl}/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      media_id: mediaId,
    }),
  })

  if (!response.ok) {
    console.error("API failed to delete media")
    return json({ error: "Failed to delete media in backend" }, { status: 500 })
  }

  const data = await response.json()

  return json(data)
}
