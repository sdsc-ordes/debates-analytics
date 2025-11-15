<script lang="ts">
    import type { PageData } from "./$types";
    import { FileIcon } from 'lucide-svelte';
    import { FileUpload } from '@skeletonlabs/skeleton-svelte';
    import { useListCollection, Listbox } from '@skeletonlabs/skeleton-svelte';

    interface Props {
        data: PageData;
    }

    let { data }: Props = $props();
    const mediaList: { label: string; value: string }[] = data?.mediaList || [];

    // --- Upload State ---
    // This state variable will be bound to the FileUpload component to capture accepted files.
    let acceptedFiles: File[] = $state([]);

    // --- Media List (existing logic) ---
    let query = $state('');
    const collection = $derived(
        useListCollection({
            items: mediaList.filter((item) => item.label.toLowerCase().includes(query.toLowerCase())),
            itemToString: (item) => item.label,
            itemToValue: (item) => item.value,
        }),
    );
</script>

<svelte:head>
    <title>Jobs</title>
    <meta name="description" content="Transcript Jobs" />
</svelte:head>

<section>
    <div class="info">

        <div class="links">
            <a href="YOUR_GITHUB_LINK_HERE" aria-label="GitHub Repository Link">
                <FileIcon class="size-6 text-[var(--primary-dark-color)]" />
            </a>
        </div>

        <h1>Job List</h1>

        <!-- Listbox (Existing code) -->
        <Listbox class="w-full max-w-md mt-8" {collection}>
            <Listbox.Label>Search for job id</Listbox.Label>
            <Listbox.Input placeholder="Type to search..." value={query} oninput={(e) => (query = e.currentTarget.value)} />
            <Listbox.Content>
                {#each collection.items as item (item.value)}
                    <Listbox.Item {item}>
                        <Listbox.ItemText>{item.label}</Listbox.ItemText>
                        <Listbox.ItemIndicator />
                    </Listbox.Item>
                {/each}
            </Listbox.Content>
        </Listbox>

    </div>
</section>

<style>
    /* Styling copied from the previous exchange to match the page theme */
    section {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        flex: 0.6;
    }

    .links {
        display: flex;
        flex-direction: row;
        justify-content: end;
        width: 100%;
        align-items: end;
        gap: 2rem;
    }

    h1 {
        font-family: var(--body-font);
        font-size: 36px;
        color: var(--primary-dark-color);
        line-height: 1;
        font-weight: bold;
    }

    .info {
        border: 2px dashed var(--primary-dark-color);
        padding: 50px;
        color: var(--text-color);
        margin-top: 1rem;
        border-radius: 10px;
        width: 90%;
        max-width: 800px;
        justify-content: start;
        align-items: start;
        display: flex;
        flex-direction: column;
        gap: 2rem;
    }
</style>
