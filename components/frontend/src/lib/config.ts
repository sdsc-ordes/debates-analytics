import { env } from "$env/dynamic/public"

export const BackendUrl = env.PUBLIC_BACKEND_SERVER || "http://backend:8000"

export const SearchPageSize = env.PUBLIC_SEARCH_PAGE_SIZE
  ? parseInt(env.PUBLIC_SEARCH_PAGE_SIZE)
  : 20
