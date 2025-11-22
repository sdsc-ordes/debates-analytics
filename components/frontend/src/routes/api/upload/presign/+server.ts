import { json } from '@sveltejs/kit';

export async function POST({ request, fetch }) {
    // 1. Get the filename from the frontend
    const { filename, contentType } = await request.json();

    // 2. Ask FastAPI for the Presigned URL
    // Make sure this URL matches your actual FastAPI route
    const fastApiUrl = 'http://backend:8000/upload/presigned-url'; 
    
    const response = await fetch(fastApiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename, content_type: contentType })
    });

    if (!response.ok) {
        console.error("FastAPI Error:", await response.text());
        return json({ error: 'Failed to generate S3 signature' }, { status: 500 });
    }

    const data = await response.json();

    // 3. Return the S3 details to the frontend
    // Expected structure: { postUrl: "...", fields: { ... }, s3Key: "..." }
    return json(data);
}
