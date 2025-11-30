import { json } from "@sveltejs/kit";
import { BackendUrl } from "$lib/config"

export async function GET({ params, fetch }) {
  // 1. Extract mediaId from the folder name [mediaId]
  const { mediaId } = params;

  if (!mediaId) {
    return json({ error: "Missing media ID" }, { status: 400 });
  }

  const targetUrl = `${BackendUrl}/upload/status/${mediaId}`;

  console.log(`Polling Backend: ${targetUrl}`);

  try {
    const response = await fetch(targetUrl, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      // Pass the 404 from Python through to the frontend
      if (response.status === 404) {
          return json({ error: "Media not found" }, { status: 404 });
      }
      console.error(`Backend returned ${response.status}`);
      return json({ error: "Failed to get status" }, { status: response.status });
    }

    const data = await response.json();
    return json(data);

  } catch (err) {
    console.error("Network error polling backend:", err);
    return json({ error: "Backend unreachable" }, { status: 502 });
  }
}