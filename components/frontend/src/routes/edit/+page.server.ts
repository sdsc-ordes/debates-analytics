import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ cookies, url }) => {
    // 1. Set the cookie that your hooks.server.ts expects.
    // Since the user reached this code, they passed the Proxy Auth.
    cookies.set('session_id', 'editor-secret', {
        path: '/',
        httpOnly: true,
        // secure: true, // Uncomment this in production (HTTPS)
        maxAge: 60 * 60 * 24 // 1 day
    });

    // 2. Redirect them to the Dashboard (or wherever they were going)
    const returnTo = url.searchParams.get('returnTo') || '/';
    throw redirect(303, returnTo);
};
