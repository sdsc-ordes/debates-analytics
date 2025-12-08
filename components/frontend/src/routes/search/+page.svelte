<script lang="ts">
  import SearchForm from "$lib/components/SearchForm.svelte";
  import FacetCounts from "$lib/components/FacetCounts.svelte";
  import SearchResultContainer from "$lib/components/SearchResultContainer.svelte";
  import { onMount } from "svelte";
  import { client } from '$lib/api/client';

  import type { components } from '$lib/api/schema';
  type SearchQuery = components['schemas']['SearchQuery'];
  type SearchDocument = components['schemas']['SearchDocument'];
  type FacetField = components['schemas']['FacetField'];

  // --- State ---
  let searchQuery: SearchQuery = $state(createDefaultSearchQuery());

  let docs = $state<SearchDocument[]>([]);
  let facets = $state<FacetField[]>([]);
  let highlighting = $state<any>({});
  let total = $state<number>(0);

  let errorMessage = $state<string | null>(null);

  const DEFAULT_FACET_FIELDS = [
      "debate_schedule",
      "statement_type",
      "debate_session",
      "speaker_name",
      "speaker_role_tag",
  ];

  function createDefaultSearchQuery(): SearchQuery {
    return {
      queryTerm: "",
      sortBy: "",
      facetFields: [],
      facetFilters: [],
    }
  }

  async function handleSearch() {
    errorMessage = null;

    try {
      const { data, error } = await client.POST("/search/search-solr", {
        body: {
            queryTerm: searchQuery.queryTerm,
            sortBy: searchQuery.sortBy,
            facetFields: DEFAULT_FACET_FIELDS,
            facetFilters: searchQuery.facetFilters
        }
      });

      if (error) {
        console.error("Search API Error:", error);
        errorMessage = "Search failed. Please try again.";
        return;
      }

      docs = data.items;
      facets = data.facets;
      highlighting = data.highlighting;
      total = data.total;

    } catch (err: any) {
      console.error("Network Error:", err);
      errorMessage = "Network error connecting to search service.";
    }
  }

  function handleReset() {
    searchQuery = createDefaultSearchQuery();
    handleSearch();
  }

  onMount(() => {
    handleReset();
  });
</script>

<svelte:head>
  <title>Political Debates Search</title>
</svelte:head>

<div class="container">
  <div class="row">
    <div class="col-md-4">
      <SearchForm
        bind:searchQuery={searchQuery}
        onsubmit={handleSearch}
        onreset={handleReset}
      />

      {#if facets && facets.length > 0}
      <FacetCounts
        bind:searchQuery={searchQuery}
        onSearch={handleSearch}
        facets={facets}
      />
      {/if}
    </div>

    {#if docs.length > 0}
      <div class="col-md-8">
        <div class="mb-3">Found {total} results</div>
        <SearchResultContainer
          {docs}
          {highlighting}
        />
      </div>
    {/if}
  </div>
</div>