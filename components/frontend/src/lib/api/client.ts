import createClient from "openapi-fetch"
import type { paths } from "./schema"
import { browser } from "$app/environment"
import { BackendUrl } from "$lib/config"

export const client = createClient<paths>({
  baseUrl: browser ? "/api" : BackendUrl,
})
