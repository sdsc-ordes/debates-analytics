<script lang="ts">
  import type { SolrQuery, SolrFacetCounts } from "$lib/interfaces/search.interface";
  import { displayIsoDate } from "$lib/utils/displayUtils";
  import { SearchXIcon } from 'lucide-svelte';

  interface Props {
    solrQuery: SolrQuery;
    facetCounts: SolrFacetCounts;
    onSearch: (solrQuery: SolrQuery) => void;
  }

  let { solrQuery = $bindable(), facetCounts, onSearch }: Props = $props();

  // --- Display Logic ---
  const displayFunctions: Record<string, (label: string) => string> = {
    debate_schedule: displayIsoDate,
  };

  function getLabel(fieldKey: string, label: string): string {
    const formatter = displayFunctions[fieldKey];
    return formatter ? formatter(label) : label;
  }

  // --- Data Transformation ($derived) ---
  // Calculates the list of fields/facets automatically when facetCounts changes
  let processedFields = $derived.by(() => {
    if (!facetCounts?.facet_fields) return [];

    const fields = [];
    for (const [key, values] of Object.entries(facetCounts.facet_fields)) {
      const facets = [];
      for (let i = 0; i < values.length; i += 2) {
        // Create the object structure expected by your template
        facets.push({ label: values[i], count: values[i + 1] });
      }
      fields.push({ key, facets });
    }
    return fields;
  });

  // --- Actions ---
  function handleFacetAddClick(facetField: string, facetValue: string) {
    if (!solrQuery.facetFieldValues) {
      solrQuery.facetFieldValues = [];
    }
    solrQuery.facetFieldValues.push({ facetField, facetValue });
    onSearch(solrQuery);
  }

  function handleFacetRemoveClick(facetField: string, facetValue: string) {
    if (!solrQuery.facetFieldValues) return;

    solrQuery.facetFieldValues = solrQuery.facetFieldValues.filter(
      (facet) => !(facet.facetField === facetField && facet.facetValue === facetValue)
    );
    onSearch(solrQuery);
  }

  function isActive(facetField: string, facetLabel: string): boolean {
    return solrQuery.facetFieldValues?.some(
      (facet) => facet.facetField === facetField && facet.facetValue === facetLabel
    ) ?? false;
  }
</script>

{#if facetCounts}
  <div class="filters">
    {#each processedFields as field}
    {#if field.facets.length > 0}
      <h4 class="facet-title">
        {field.key.replace(/_/g, " ")}
      </h4>
      <div class="facets">
        {#each field.facets as facet}
          {#if facet.count && facet.label}
            <div class="facet-row">
              <button
                class="facet-item {isActive(field.key, String(facet.label)) ? 'active' : ''}"
                onclick={() => isActive(field.key, String(facet.label))
                  ? handleFacetRemoveClick(field.key, String(facet.label))
                  : handleFacetAddClick(field.key, String(facet.label))
                }
              >
                {getLabel(field.key, String(facet.label))}
                {#if isActive(field.key, String(facet.label))}
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
    {/if}
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
