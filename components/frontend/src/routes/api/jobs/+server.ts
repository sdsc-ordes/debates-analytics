import { json } from '@sveltejs/kit';

export async function POST({ request }) {
    // 1. Receive the JSON from the frontend
    const { s3Key, title } = await request.json();

    // 2. Forward this to your FastAPI backend
    // Assuming FastAPI is running on port 8000 in docker
    const fastApiUrl = 'http://backend:8000/process'; 

    const response = await fetch(fastApiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ s3_key: s3Key }) // Match FastAPI expected schema
    });

    if (!response.ok) {
        return json({ error: 'Failed to queue job' }, { status: 500 });
    }

    const data = await response.json();
    
    // Return the job ID to the frontend
    return json(data);
}
