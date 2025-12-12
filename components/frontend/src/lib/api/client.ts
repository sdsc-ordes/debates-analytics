import createClient from "openapi-fetch";
import type { paths } from "./schema";
import { browser } from "$app/environment";
import { env } from '$env/dynamic/public';

// Logic:
// 1. If PUBLIC_BACKEND_SERVER is set (e.g., in your local .env), use it.
// 2. If not set, fall back to Docker defaults:
//    - Browser -> '/api' (proxied)
//    - Server  -> 'http://backend:8000' (internal Docker DNS)
const baseUrl = env.PUBLIC_BACKEND_SERVER || (browser ? "/api" : "http://backend:8000");

export const client = createClient<paths>({
  baseUrl: baseUrl,
});
