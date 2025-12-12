<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import SearchForm from "$lib/components/SearchForm.svelte";
  import FacetCounts from "$lib/components/FacetCounts.svelte";
  import SearchResultContainer from "$lib/components/SearchResultContainer.svelte";
  import { client } from '$lib/api/client';

  import type { components } from '$lib/api/schema';
  type SearchQuery = components['schemas']['SearchQuery'];
  type SearchDocument = components['schemas']['SearchDocument'];
  type FacetField = components['schemas']['FacetField'];
  type FacetFilter = NonNullable<SearchQuery['facetFilters']>[number];

  const DEFAULT_FACET_FIELDS = [
      "debate_schedule",
      "statement_type",
      "debate_session",
      "speaker_name",
      "speaker_role_tag",
      "statement_language",
  ];

  // Helper to parse URL params into a SearchQuery object
  function getQueryFromUrl(): SearchQuery {
    const params = $page.url.searchParams;
    const rawFilters = params.getAll('facetFilters');

    const parsedFilters: FacetFilter[] = rawFilters.map(f => {
        const [field, val] = f.split(':', 2);
        return { facetField: field, facetValue: val };
    });

    return {
      queryTerm: params.get('queryTerm') || "",
      sortBy: params.get('sortBy') || "",
      facetFields: DEFAULT_FACET_FIELDS,
      facetFilters: parsedFilters,
    };
  }

  // Reactive State
  let searchQuery = $state<SearchQuery>(getQueryFromUrl());
  let docs = $state<SearchDocument[]>([]);
  let facets = $state<FacetField[]>([]);
  let highlighting = $state<any>({});
  let total = $state<number>(0);
  let errorMessage = $state<string | null>(null);

  // Solr Search query
  async function performFetch(query: SearchQuery) {
    errorMessage = null;
    const stringFilters = (query.facetFilters || []).map(
        (f: any) => `${f.facetField}:${f.facetValue}`
    );

    try {
      const { data, error } = await client.GET("/search/search-solr", {
        params: {
            query: {
                queryTerm: query.queryTerm,
                sortBy: query.sortBy,
                facetFields: DEFAULT_FACET_FIELDS,
                facetFilters: stringFilters,
            }
        }
      });

      if (error) {
        console.error("Search API Error:", error);
        errorMessage = "Search failed.";
        return;
      }
      console.log("data", data);

      docs = data?.docs ?? [];
      facets = data?.facets ?? [];
      highlighting = data?.highlighting ?? {};
      total = data?.total ?? 0;

    } catch (err: any) {
      console.error("Network Error:", err);
      errorMessage = "Network error.";
    }
  }

  // TO avoid a loop read into a local variable
  $effect(() => {
     const nextQuery = getQueryFromUrl();
     searchQuery = nextQuery;
     performFetch(nextQuery);
  });

  // User Actions
  function handleUpdateUrl() {
    const params = new URLSearchParams();
    if (searchQuery.queryTerm) params.set('queryTerm', searchQuery.queryTerm);

    if (searchQuery.facetFilters) {
        searchQuery.facetFilters.forEach((f: any) => {
            params.append('facetFilters', `${f.facetField}:${f.facetValue}`);
        });
    }

    // This updates the URL -> Triggers $effect above
    goto(`?${params.toString()}`, { keepFocus: true, noScroll: true });
  }

  function handleReset() {
    goto('?', { keepFocus: true });
  }
</script>

<svelte:head>
  <title>Political Debates Search</title>
</svelte:head>

<div class="container">
  <div class="row">
    <div class="col-md-4">
      <SearchForm
        bind:searchQuery={searchQuery}
        onsubmit={handleUpdateUrl}
        onreset={handleReset}
      />

      {#if facets && facets.length > 0}
      <FacetCounts
        bind:searchQuery={searchQuery}
        onSearch={handleUpdateUrl}
        facets={facets}
      />
      {/if}
    </div>

    <div class="col-md-8">
      {#if errorMessage}
        <div class="alert alert-danger">{errorMessage}</div>
      {/if}

      {#if docs.length > 0}
        <div class="mb-3">Found {total} results</div>
        <SearchResultContainer
          {docs}
          {highlighting}
        />
      {:else if !errorMessage}
        <p>No results found.</p>
      {/if}
    </div>
  </div>
</div>
