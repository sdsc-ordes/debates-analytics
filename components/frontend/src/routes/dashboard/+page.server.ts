import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ fetch }) => {
  console.log("Server Load: Fetching media list...");

  try {
    const res = await fetch(`/api/metadata/list`);

    if (!res.ok) {
      console.error(`Backend error: ${res.status}`);
      return { mediaItems: [], error: "Failed to fetch from backend" };
    }

    const data = await res.json();

    // 2. Sort on the server
    const sortedItems = data.items.sort((a: any, b: any) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );

    // 3. Return data to the page
    return {
      mediaItems: sortedItems,
      error: null
    };

  } catch (err) {
    console.error("Network error in load function:", err);
    return { mediaItems: [], error: "Backend unreachable" };
  }
};
