<script lang="ts">
  import type { components } from '$lib/api/schema';
  import { displayIsoDate } from "$lib/utils/displayUtils";

  type SearchQuery = components['schemas']['SearchQuery'];
  type FacetField = components['schemas']['FacetField'];
  type FacetFilter = NonNullable<SearchQuery['facetFilters']>[number];

  interface Props {
    searchQuery: SearchQuery;
    facets: FacetField[];
    onSearch: (solrRequest: SearchQuery) => void;
  }

  let { searchQuery = $bindable(), facets, onSearch }: Props = $props();

  const displayFunctions: Record<string, (label: string) => string> = {
    debate_schedule: displayIsoDate,
  };

  function getLabel(fieldKey: string, label: string): string {
    const formatter = displayFunctions[fieldKey];
    return formatter ? formatter(label) : label;
  }

  function handleFacetAddClick(facetField: string, facetValue: string) {
    // 1. Create the new filter object
    // Casting 'as FacetFilter' keeps TypeScript happy if the schema is strict
    const newFilter = { facetField, facetValue } as FacetFilter;

    // 2. Immutable Update (Better for Svelte Reactivity)
    // Create a NEW array instead of .push()
    searchQuery.facetFilters = [
        ...(searchQuery.facetFilters || []),
        newFilter
    ];

    // 3. Trigger Search
    onSearch(searchQuery);
  }

  function isSameDate(storedValue: string, uiValue: string): boolean {
    // 1. Normalize the stored value (e.g. 2025-12-13T16 -> 2025-12-13)
    // This prevents "Invalid Date" errors in JS
    const cleanStored = storedValue.length >= 10 ? storedValue.substring(0, 10) : storedValue;

    const dateA = new Date(cleanStored);
    const dateB = new Date(uiValue);

    // 2. Check validity
    if (isNaN(dateA.getTime()) || isNaN(dateB.getTime())) {
      return false;
    }

    // 3. Compare just the Date string (ignoring time completely)
    return dateA.toDateString() === dateB.toDateString();
  }

  function handleFacetRemoveClick(facetField: string, facetValue: string) {
    if (!searchQuery.facetFilters) return;

    searchQuery.facetFilters = searchQuery.facetFilters.filter((facet) => {
      // A. Standard Exact Match (Return FALSE to remove)
      if (facet.facetField === facetField && facet.facetValue === facetValue) {
        return false;
      }

      // B. Date Logic (Reusing the helper)
      if (facetField === 'debate_schedule' && facet.facetField === 'debate_schedule') {
        // If dates match, return FALSE to remove it
        if (isSameDate(facet.facetValue, facetValue)) {
          return false;
        }
      }

      // Keep everything else
      return true;
    });

    onSearch(searchQuery);
  }

  function isActive(facetField: string, facetLabel: string): boolean {
    return searchQuery.facetFilters?.some((facet) => {
      // A. Standard Exact Match
      if (facet.facetField === facetField && facet.facetValue === facetLabel) {
        return true;
      }

      // B. Date Logic (Reusing the helper)
      if (facetField === 'debate_schedule' && facet.facetField === 'debate_schedule') {
        return isSameDate(facet.facetValue, facetLabel);
      }

      return false;
    }) ?? false;
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
          {#if facet.label}
          <div class="facet-row">
            <button
              class="facet-item {isActive(field.field_name, facet.label) ? 'active' : ''}"
              onclick={() => isActive(field.field_name, facet.label)
                ? handleFacetRemoveClick(field.field_name, facet.label)
                : handleFacetAddClick(field.field_name, facet.label)
              }
              type="button"
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
          {/if}
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