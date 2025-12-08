<script lang="ts">
    import { goto } from '$app/navigation';
    import { replaceWithHighlightedVersion } from '$lib/utils/highlightSearchTerms';
    import type { components } from '$lib/api/schema';
    import {
        formatTimeForDisplay,
        displayIsoDate,
    } from "$lib/utils/displayUtils";

    type SearchDocument = components['schemas']['SearchDocument'];
    type HighlightedDoc = components['schemas']['HighlightedDoc'];
    interface Props {
        highlighting: Record<string, HighlightedDoc>;
        doc: SearchDocument;
    }

    let { highlighting, doc }: Props = $props();
    let docId: string = doc.id;

    const navigateToVideoPlayer = () => {
        goto(`/mediaplayer/${encodeURIComponent(doc.media_id)}?start=${encodeURIComponent(doc.start)}`);
    };

    const get_debate_title = () => {
        if (doc.debate_session && doc.debate_type) {
            return `${doc.debate_session} ${doc.debate_type}`
        } else if (doc.debate_session) {
            return doc.debate_session
        } else {
            return doc.media_id
        }
    }
</script>

<div class="statement">
    <div
        class="card"
        onclick={() => navigateToVideoPlayer()}
        role="button"
        tabindex="0"
        onkeydown={(e) =>
            (e.key === "Enter" || e.key === " ") &&
            navigateToVideoPlayer()}
    >
        <div class="card-body">
            <div class="card-title-large">
                {get_debate_title()}
            </div>
            <p class="card-body-large truncated">
                {#if highlighting}
                    {@html replaceWithHighlightedVersion(
                        doc.statement,
                        highlighting[docId]?.statement ?? []
                    ).join(" ")}
                {:else}
                    {doc.statement.join(" ")}
                {/if}
            </p>
            <div class="datetime-container">
                {#if doc.debate_schedule}
                <div class="date-time-item">
                    <i class="fa fa-calendar" aria-hidden="true"></i>
                    <small class="card-subtle"
                        >{displayIsoDate(doc.debate_schedule)}</small
                    >
                </div>
                {/if}
                <div class="date-time-item">
                    <i class="fa fa-clock" aria-hidden="true"></i>
                    <small class="card-subtle"
                        >{formatTimeForDisplay(doc.start)} - {formatTimeForDisplay(
                            doc.end,
                        )}</small
                    >
                </div>
                <small class="card-subtle">{doc.statement_type}
                    {#if doc.statement_language}
                        ({doc.statement_language})
                    {/if}</small
                >
            </div>
        </div>
    </div>
</div>

<style>
    .datetime-container {
        display: flex;
        gap: 1rem;
        align-items: center;
    }

    .card-body-large.truncated {
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .card:hover {
        box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.1);
    }

    .date-time-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .fa {
        font-size: 1rem;
        color: grey;
    }

</style>
