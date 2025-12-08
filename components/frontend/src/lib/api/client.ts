import createClient from "openapi-fetch";
import type { paths } from "./schema";
import { browser } from '$app/environment';

// 1. Dynamic Base URL
// Browser -> Use Proxy ('/api')
// Server (Docker) -> Talk directly to Python Backend ('http://backend:8000')
const baseUrl = browser ? "/api" : "http://backend:8000";

export const client = createClient<paths>({
    baseUrl: baseUrl,
});
