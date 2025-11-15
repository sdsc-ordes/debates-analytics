import { fetchUploadUrl } from "$lib/server/fetchUploadUrl"
import { logger } from '$lib/utils/logger'

export async function POST({ request }) {
  try {
    const bodyObject = await request.json();
    const filename = bodyObject.filename;
    logger.info({filename: filename}, "filename in api")
    const response = await fetchUploadUrl(filename)
    logger.info({response: response}, "response from api")
    return new Response(JSON.stringify({ raw_response: response }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    })
  } catch (error) {
    logger.error({error: error}, "API Error:")
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
    })
  }
}
