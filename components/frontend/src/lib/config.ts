import { PUBLIC_BACKEND_SERVER } from "$env/static/public"
import { PUBLIC_SOLR_PAGE_SIZE } from "$env/static/public"

export const BackendUrl = PUBLIC_BACKEND_SERVER
export const SolrPageSize = parseInt(PUBLIC_SOLR_PAGE_SIZE)
