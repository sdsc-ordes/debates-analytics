<script>
    import { page } from '$app/stores';
</script>

<div>
    <h2>It seems there has been an error, sorry about that.</h2>
    {#if $page?.error}
        <div class="mt-4 p-4 border-y-2">
            {#if $page?.status}
                <p>Page status: {$page?.status}</p>
                <a href="/search">Return to Search Page</a>
            {/if}
            {#if $page?.error?.message}
                <p>Error message: {$page?.error?.message}</p>
            {/if}
        </div>
    {/if}
</div>
