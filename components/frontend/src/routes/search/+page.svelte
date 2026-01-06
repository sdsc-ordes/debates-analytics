<script lang="ts">
  import { goto } from "$app/navigation"
  import { page } from "$app/state"
  import SearchForm from "$lib/components/SearchForm.svelte"
  import FacetCounts from "$lib/components/FacetCounts.svelte"
  import SearchResultContainer from "$lib/components/SearchResultContainer.svelte"
  import { client } from "$lib/api/client"
  import { SolrPageSize } from "$lib/config"

  import type { components } from "$lib/api/schema"
  type SearchDocument = components["schemas"]["SearchDocument"]
  type FacetField = components["schemas"]["FacetField"]

  interface FacetFilter {
    facetField: string
    facetValue: string
  }

  interface SearchQuery {
    queryTerm: string
    sortBy?: string
    facetFields?: string[]
    facetFilters?: FacetFilter[]
    page?: number
  }

  const DEFAULT_FACET_FIELDS = [
    "debate_schedule",
    "statement_type",
    "debate_session",
    "debate_type",
    "speaker_name",
    "speaker_role_tag",
    "statement_language",
    "media_id",
  ]

  const rowsPerPage = SolrPageSize

  // Helper to parse URL params into a SearchQuery object
  function getQueryFromUrl(): SearchQuery {
    const params = page.url.searchParams
    const rawFilters = params.getAll("facetFilters")

    const parsedFilters: FacetFilter[] = rawFilters.map((f) => {
      const [field, val] = f.split(":", 2)
      return { facetField: field, facetValue: val }
    })

    return {
      queryTerm: params.get("queryTerm") || "",
      sortBy: params.get("sortBy") || "",
      facetFields: DEFAULT_FACET_FIELDS,
      facetFilters: parsedFilters,
      page: parseInt(params.get("page") || "1", 10) || 1,
    }
  }

  // Reactive State
  let searchQuery = $state<SearchQuery>(getQueryFromUrl())
  let docs = $state<SearchDocument[]>([])
  let facets = $state<FacetField[]>([])
  let highlighting = $state<any>({})
  let total = $state<number>(0)
  let errorMessage = $state<string | null>(null)

  // derived values
  const totalPages = $derived(Math.ceil(total / rowsPerPage));
  const startResult = $derived(
    total === 0 ? 0 : ((searchQuery.page || 1) - 1) * rowsPerPage + 1
  );

  const endResult = $derived(
    Math.min((searchQuery.page || 1) * rowsPerPage, total)
  );

  function getPaginationRange(current: number, max: number) {
    // If few pages, show all
    if (max <= 7) return Array.from({ length: max }, (_, i) => i + 1);

    const pages: (number | string)[] = [];
    const radius = 2; // How many pages to show around the current page

    // Always show Page 1
    pages.push(1);

    if (current > radius + 2) pages.push('...');

    // Middle pages
    let start = Math.max(2, current - radius);
    let end = Math.min(max - 1, current + radius);

    for (let i = start; i <= end; i++) {
        pages.push(i);
    }

    if (current < max - (radius + 1)) pages.push('...');

    // Always show Last Page
    pages.push(max);

    return pages;
  }

  function goToPage(p: number | string) {
    if (typeof p === 'string') return;
    if (p < 1 || p > totalPages) return;

    searchQuery.page = p as number;
    handleUpdateUrl();
  }

  async function performFetch(query: SearchQuery) {
    errorMessage = null
    const stringFilters = (query.facetFilters || []).map(
      (f: any) => `${f.facetField}:${f.facetValue}`,
    )
    const pageNum = query.page || 1;
    const startOffset = (pageNum - 1) * rowsPerPage;

    try {
      const { data, error } = await client.GET("/search/search-solr", {
        params: {
          query: {
            queryTerm: query.queryTerm,
            sortBy: query.sortBy,
            facetFields: DEFAULT_FACET_FIELDS,
            facetFilters: stringFilters,
            rows: rowsPerPage,
            start: startOffset,
          },
        },
      })

      if (error) {
        console.error("Search API Error:", error)
        errorMessage = "Search failed."
        return
      }
      console.log("data", data)

      docs = data?.docs ?? []
      facets = data?.facets ?? []
      highlighting = data?.highlighting ?? {}
      total = data?.total ?? 0
    } catch (err: any) {
      console.error("Network Error:", err)
      errorMessage = "Network error."
    }
  }

  // TO avoid a loop read into a local variable
  $effect(() => {
    const nextQuery = getQueryFromUrl()
    searchQuery = nextQuery
    performFetch(nextQuery)
  })

  // User Actions
  function handleUpdateUrl() {
    const params = new URLSearchParams()
    if (searchQuery.queryTerm) params.set("queryTerm", searchQuery.queryTerm)

    if (searchQuery.facetFilters) {
      searchQuery.facetFilters.forEach((f: any) => {
        params.append("facetFilters", `${f.facetField}:${f.facetValue}`)
      })
    }

    if (searchQuery.page && searchQuery.page > 1) {
      params.set("page", searchQuery.page.toString())
    }

    // This updates the URL -> Triggers $effect above
    goto(`?${params.toString()}`, { keepFocus: true, noScroll: true })
  }

  function handleNewSearch() {
    searchQuery.page = 1
    handleUpdateUrl()
  }

  function handleReset() {
    goto("?", { keepFocus: true })
  }
</script>

<svelte:head>
  <title>Political Debates Search</title>
</svelte:head>

<div class="container">
  <div class="row">
    <div class="col-md-4">
      <SearchForm
        bind:searchQuery
        onsubmit={handleNewSearch}
        onreset={handleReset}
      />

      {#if facets && facets.length > 0}
        <FacetCounts bind:searchQuery onSearch={handleNewSearch} {facets} />
      {/if}
    </div>

    <div class="col-md-8">
      {#if errorMessage}
        <div class="alert alert-danger">{errorMessage}</div>
      {/if}

      {#if docs.length > 0}
        <div class="mb-3">
          {#if total > 0}
            {startResult}-{endResult} / {total}
          {:else}
            0 results
          {/if}
        </div>
        {#if total > rowsPerPage }
        <nav aria-label="Page navigation">
          <ul class="pagination">
            <li class="page-item" class:disabled={searchQuery.page === 1}>
              <button
                class="page-link"
                onclick={() => goToPage(searchQuery.page - 1)}
                aria-label="Previous"
              >
                <span aria-hidden="true">&laquo;</span>
              </button>
            </li>

            {#each getPaginationRange(searchQuery.page || 1, totalPages) as p}
              <li
                class="page-item"
                class:active={p === searchQuery.page}
                class:disabled={p === "..."}
              >
                <button class="page-link" onclick={() => goToPage(p)}>
                  {p}
                </button>
              </li>
            {/each}

            <li
              class="page-item"
              class:disabled={searchQuery.page === totalPages}
            >
              <button
                class="page-link"
                onclick={() => goToPage((searchQuery.page || 1) + 1)}
                aria-label="Next"
              >
                <span aria-hidden="true">&raquo;</span>
              </button>
            </li>
          </ul>
        </nav>
        {/if}
        <SearchResultContainer
          {docs}
          {highlighting}
          queryTerm={searchQuery.queryTerm}
        />
      {:else if !errorMessage}
        <p>No results found.</p>
      {/if}
    </div>
  </div>
</div>
