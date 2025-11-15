<script lang="ts">
    import type { PageData } from "./$types";
	import { FileIcon } from 'lucide-svelte';
	import { FileUpload } from '@skeletonlabs/skeleton-svelte';
	import { Listbox, useListCollection } from '@skeletonlabs/skeleton-svelte';
    interface Props {
        data: PageData;
    }

    let { data }: Props = $props();
    $inspect("data", data);
    console.log("data", data);
    const mediaList: { label: string; value: string }[] = data?.mediaList || [];
    console.log("mediaList", mediaList);

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
	<title>Upload</title>
	<meta name="description" content="File upload" />
</svelte:head>

<section>

<h1>Video Upload</h1>

    <FileUpload>
        <FileUpload.Label>Upload your files</FileUpload.Label>
        <FileUpload.Dropzone>
            <FileIcon class="size-10" />
            <span>Select file or drag here.</span>
            <FileUpload.Trigger
               class="button-primary"
            >
               Browse Files
            </FileUpload.Trigger>
            <FileUpload.HiddenInput />
        </FileUpload.Dropzone>
        <FileUpload.ItemGroup>
            <FileUpload.Context>
                {#snippet children(fileUpload)}
                    {#each fileUpload().acceptedFiles as file (file.name)}
                        <FileUpload.Item {file}>
                            <FileUpload.ItemName>{file.name}</FileUpload.ItemName>
                            <FileUpload.ItemSizeText>{file.size} bytes</FileUpload.ItemSizeText>
                            <FileUpload.ItemDeleteTrigger />
                        </FileUpload.Item>
                    {/each}
                {/snippet}
            </FileUpload.Context>
        </FileUpload.ItemGroup>
    </FileUpload>

    <Listbox class="w-full max-w-md" {collection}>
        <Listbox.Label>Search for Food</Listbox.Label>
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

</section>
