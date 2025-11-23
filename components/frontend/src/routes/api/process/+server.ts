import { json } from '@sveltejs/kit';
import { BackendUrl } from "$lib/config"

export async function POST({ request, fetch }) {
    const { s3Key, jobId, title } = await request.json();
    console.log(`Sending processing request for S3 key: ${s3Key}, job ID: ${jobId}`);

    const response = await fetch(`${BackendUrl}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            s3_key: s3Key,
            media_id: jobId,
            title: title,
        })
    });

    if (!response.ok) {
        console.error("API failed to queue job");
        return json({ error: 'Failed to queue job in backend' }, { status: 500 });
    }

    const data = await response.json();

    return json(data);
}
