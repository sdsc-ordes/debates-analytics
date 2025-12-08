<script lang="ts">
  import type { components } from '$lib/api/schema';
  import { displayIsoDate } from "$lib/utils/displayUtils";

  // Update types to match the new clean backend structure
  type SearchQuery = components['schemas']['SearchQuery'];
  type FacetField = components['schemas']['FacetField'];

  interface Props {
    searchQuery: SearchQuery;
    facets: FacetField[]; // Renamed from facetCounts to match the list structure
    onSearch: (solrRequest: SearchQuery) => void;
  }

  let { searchQuery = $bindable(), facets, onSearch }: Props = $props();

  // --- Display Logic ---
  const displayFunctions: Record<string, (label: string) => string> = {
    debate_schedule: displayIsoDate,
  };

  function getLabel(fieldKey: string, label: string): string {
    const formatter = displayFunctions[fieldKey];
    return formatter ? formatter(label) : label;
  }

  // --- Actions ---
  // No data transformation needed! We iterate directly over 'facets'.

  function handleFacetAddClick(facetField: string, facetValue: string) {
    if (!searchQuery.facetFilters) {
      searchQuery.facetFilters = [];
    }
    searchQuery.facetFilters.push({ facetField, facetValue });
    onSearch(searchQuery);
  }

  function handleFacetRemoveClick(facetField: string, facetValue: string) {
    if (!searchQuery.facetFilters) return;

    searchQuery.facetFilters = searchQuery.facetFilters.filter(
      (facet) => !(facet.facetField === facetField && facet.facetValue === facetValue)
    );
    onSearch(searchQuery);
  }

  function isActive(facetField: string, facetLabel: string): boolean {
    return searchQuery.facetFilters?.some(
      (facet) => facet.facetField === facetField && facet.facetValue === facetLabel
    ) ?? false;
  }
</script>

{#if facets && facets.length > 0}
  <div class="filters">
    {#each facets as field}
      <h4 class="facet-title">
        {field.field_name.replace(/_/g, " ")}
      </h4>

      <div class="facets">
        {#each field.values as facet}
          <div class="facet-row">
            <button
              class="facet-item {isActive(field.field_name, facet.label) ? 'active' : ''}"
              onclick={() => isActive(field.field_name, facet.label)
                ? handleFacetRemoveClick(field.field_name, facet.label)
                : handleFacetAddClick(field.field_name, facet.label)
              }
            >
              {getLabel(field.field_name, facet.label)}

              {#if isActive(field.field_name, facet.label)}
                <span class="remove-icon">
                  <i class="fa fa-xmark" aria-hidden="true"></i>
                </span>
              {/if}
            </button>

            <small class="card-subtle">{facet.count}</small>
          </div>
        {/each}
      </div>
    {/each}
  </div>
{:else}
  <p>No facet counts available.</p>
{/if}

<style>
  .filters {
    margin-top: 1rem;
    padding: 1rem;
    border-radius: 12px;
  }

  .facets {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding-left: 1rem;
  }

  .facet-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .facet-title {
    font-family: var(--body-font);
    font-size: 16px;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
    text-transform: lowercase;
    color: var(--primary-color);
  }

  .facet-item {
    color: var(--primary-color);
    border: none;
    padding: 5px 10px;
    border-radius: 10px;
    cursor: pointer;
    transition: background-color 0.3s;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .facet-item.active {
    background-color: var(--primary-color);
    color: var(--on-primary);
    display: inline-flex;
    align-items: center;
    gap: 8px; /* Space between text and X */
    padding-right: 8px; /* Ensure padding on the right */
  }

  .remove-icon {
    display: inline-flex;
    margin-left: 6px;
    opacity: 0.9;
  }
</style>