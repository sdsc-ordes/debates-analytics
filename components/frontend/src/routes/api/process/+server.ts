import { json } from '@sveltejs/kit';

export async function POST({ request, fetch }) {
    const { s3Key, jobId, title } = await request.json();
    console.log(`Sending processing request for S3 key: ${s3Key}, job ID: ${jobId}`);

    // 1. Send the command to your FastAPI backend
    // Ensure this URL matches your Docker service name (usually 'backend')
    const fastapiRes = await fetch('http://backend:8000/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            s3_key: s3Key,
            media_id: jobId // Pass the ID if you generated it earlier, or let Backend generate it
        })
    });

    if (!fastapiRes.ok) {
        console.error("FastAPI failed to queue job");
        return json({ error: 'Failed to queue job in backend' }, { status: 500 });
    }

    const data = await fastapiRes.json();
    
    // 2. Return success to Frontend
    return json(data);
}
