import type { components } from "$lib/api/schema"

type FacetField = components["schemas"]["FacetField"]

// Define the main Search Query object
interface SearchQuery {
  queryTerm: string
  sortBy?: string
  facetFields?: string[]
  facetFilters?: FacetFilter[]
  rows?: number
  start?: number
}

type FacetFilter = NonNullable<
  components["schemas"]["SearchQuery"]["facetFilters"]
>[number]

export type { SearchQuery }
