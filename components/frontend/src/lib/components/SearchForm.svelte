<script lang="ts">
    import type { components } from '$lib/api/schema';
    type searchQuery = components['schemas']['SearchQuery'];

    let {
        searchQuery = $bindable(),
        onsubmit,
        onreset
    }: {
        searchQuery: searchQuery;
        onsubmit?: () => void;
        onreset?: () => void;
    } = $props();

    function handleSubmit(event: SubmitEvent) {
        event.preventDefault();
        onsubmit?.();
    }

    function handleReset() {
        searchQuery.queryTerm = "";
        onreset?.();
    }
</script>

<form onsubmit={handleSubmit} class="search-form" role="search">
    <input
        class="search-input"
        type="text"
        bind:value={searchQuery.queryTerm}
        placeholder="Enter search term"
        aria-label="Search term"
    />

    <button
        class="option-button"
        type="button"
        onclick={handleReset}
        aria-label="Clear search"
    >
        <i class="fa fa-xmark" aria-hidden="true"></i>
    </button>

    <button class="button-primary" type="submit">
        <i class="fa fa-search" aria-hidden="true"></i> Search
    </button>
</form>
<style>
    .search-form {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        width: 100%;
        max-width: 40rem;
        margin: 0 auto;
        padding: 10px;
        padding-right: 20px;
        border-radius: 50px;
        box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
        /* background-color: var(--background-color); */
    }
    .search-input {
        flex: 1;
        padding: 10px 15px;
        border: none;
        border-radius: 50px;
        font-size: 12px;
        color: var(--text-color);
        outline: none;
        transition: border-color 0.3s ease;
    }

    .option-button {
        /* margin-top: 0.5rem;
        font-size: 0.9rem; */
        color: gray;
        background: none;
        border: none;
        cursor: pointer;
        text-align: left;
        /* margin-left: 2rem; */
    }
</style>
