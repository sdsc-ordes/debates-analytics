<script lang="ts">
  import SearchResultItem from "$lib/components/SearchResultItem.svelte";
  import type { components } from '$lib/api/schema';
  type SearchDocument = components['schemas']['SearchDocument'];
  type HighlightedDoc = components['schemas']['HighlightedDoc'];

  interface Props {
    docs: SearchDocument[];
    highlighting: Record<string, HighlightedDoc>;
    queryTerm: string;
  }

  let { docs, highlighting, queryTerm }: Props = $props();

</script>

<div class="container">
  <div class="statements">
    {#if docs && docs.length > 0}
      {#each docs as doc}
        <SearchResultItem {doc} {highlighting} {queryTerm} />
      {/each}
    {:else}
      <p>No statements available.</p>
    {/if}
  </div>
</div>

<style>
  .statements {
      display: flex;
      flex-direction: column;
      gap: 1rem;
  }
</style>
