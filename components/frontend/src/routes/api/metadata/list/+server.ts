import { json } from "@sveltejs/kit";
import { BackendUrl } from "$lib/config"; // Ensure this points to http://backend:8000

export async function GET({ fetch }) {
  // REMOVED: const { mediaList } = await request.json() 
  // GET requests have no body!
  
  console.log(`Sending list media request`);

  try {
      // Based on your curl command, the path is /list
      // If you added a prefix in python (like /admin), update this to `${BackendUrl}/admin/list`
      const response = await fetch(`${BackendUrl}/list`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) {
        console.error(`Backend returned ${response.status}`);
        return json({ error: "Failed to get media list" }, { status: response.status });
      }

      const data = await response.json();
      return json(data);

  } catch (err) {
      console.error("Network error connecting to backend:", err);
      return json({ error: "Backend unreachable" }, { status: 502 });
  }
}
