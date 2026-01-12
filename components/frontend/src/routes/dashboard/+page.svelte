<script lang="ts">
  import { enhance } from '$app/forms';
  import { Trash2, FileIcon, Loader, RefreshCw, Upload, Copy, Check, ListRestart } from 'lucide-svelte';
  import type { PageData, ActionData } from './$types';
  import { invalidateAll } from '$app/navigation';
  import type { components } from '$lib/api/schema';
  type MediaListItem = components["schemas"]["MediaListItem"]

  let { data }: { data: PageData } = $props();
  $inspect("data", data);

  let items: MediaListItem[] = $derived(data.items);

  let isDeleting = $state<string | null>(null);
  let isReindexing = $state<string | null>(null);
  let copiedId = $state<string | null>(null);
  let reindexSuccessId = $state<string | null>(null);

  function formatDate(isoString: string) {
    if(!isoString) return "-";
    return new Date(isoString).toLocaleString('en-US', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  }

  function getStatusClass(status: string) {
    if (status.includes('completed') || status === 'success') return 'status-success';
    if (status.includes('failed') || status.includes('error')) return 'status-error';
    return 'status-processing';
  }

  async function copyMediaId(id: string) {
    await navigator.clipboard.writeText(id);
    copiedId = id;
    setTimeout(() => copiedId = null, 1500);
  }
</script>

<svelte:head>
  <title>Dashboard</title>
</svelte:head>

<section class="page-layout">
  <div class="dashboard-card">

    <div class="header">
      <h1>Dashboard</h1>
      <div class="actions">
      <button
          class="icon-button"
          onclick={() => invalidateAll()}
          title="Refresh List"
          type="button"
        >
          <RefreshCw class={isDeleting ? 'animate-spin' : ''} size={18} />
        </button>
        <a href="/upload" class="button-primary" style="text-decoration: none;">
          <Upload size={14} style="margin-right: 6px;" /> Upload New
        </a>
      </div>
    </div>

    {#if items.length === 0}
      <div class="state-container">
        <p class="card-title-large">No media found</p>
        <p class="card-subtle">Upload a video to get started.</p>
      </div>

    {:else}
      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>File Name</th>
              <th>Media Id</th>
              <th>Status</th>
              <th class="desktop-only">Date</th>
              <th class="text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {#each items as item (item.media_id)}
              <tr>
                <td>
                  <div class="file-cell">
                    <FileIcon size={16} color="var(--primary-color)" />
                    <span class="filename" title={item.filename}>
                      {item.filename}
                    </span>
                  </div>
                  <div class="mobile-meta card-subtle">{formatDate(item.created_at)}</div>
                </td>

                <td>
                  <div class="media-id-cell">
                    <code title={item.media_id}>{item.media_id.slice(0, 8)}...</code>
                    <button class="copy-btn" onclick={() => copyMediaId(item.media_id)} title="Copy Media ID" type="button">
                      {#if copiedId === item.media_id}
                        <Check size={14} color="#059669" />
                      {:else}
                        <Copy size={14} />
                      {/if}
                    </button>
                  </div>
                </td>

                <td>
                  <span class="badge {getStatusClass(item.status)}">
                    {item.status.replace(/_/g, ' ')}
                  </span>
                </td>

                <td class="desktop-only card-body-large">
                  {formatDate(item.created_at)}
                </td>

                <td class="text-right">
                  <form
                    method="POST"
                    action="?/delete"
                    style="display: inline;"
                    use:enhance={({ cancel }) => {
                        if (!confirm('Are you sure? This will delete files from S3, Solr, and MongoDB.')) {
                            cancel();
                            return;
                        }
                        isDeleting = item.media_id;

                        return async ({ update }) => {
                            await update();
                            isDeleting = null;
                        };
                    }}
                  >
                    <input type="hidden" name="mediaId" value={item.media_id} />

                    <button
                      class="icon-button delete-icon"
                      type="submit"
                      disabled={isDeleting === item.media_id}
                      title="Delete Media"
                    >
                      {#if isDeleting === item.media_id}
                        <Loader class="animate-spin" size={16} />
                      {:else}
                        <Trash2 size={16} />
                      {/if}
                    </button>
                  </form>
                  </td>
                  <td class="text-right">
                  <form
                    method="POST"
                    action="?/reindex"
                    style="display: inline;"
                    use:enhance={({ cancel }) => {
                        if (!confirm('Are you sure? This will reindex the media on Solr and MongoDB.')) {
                            cancel();
                            return;
                        }
                        isReindexing = item.media_id;

                        return async ({ result, update }) => {
                            await update();
                            isReindexing = null;
                            if (result.type === 'success') {
                                reindexSuccessId = item.media_id;
                                setTimeout(() => reindexSuccessId = null, 2000);
                                console.log("Server Response:", result.data);
                            } else if (result.type === 'failure') {
                              alert('Reindex failed: ' + result.data?.message);
                            }
                        };
                    }}
                  >
                    <input type="hidden" name="mediaId" value={item.media_id} />
                    <button
                      class="icon-button reindex-icon"
                      type="submit"
                      disabled={isReindexing === item.media_id}
                      title="Reindex Media"
                    >
                      {#if isReindexing === item.media_id}
                        <Loader class="animate-spin" size={16} />
                      {:else if reindexSuccessId === item.media_id}
                        <Check size={16} color="#059669" />
                      {:else}
                        <ListRestart size={16} />
                      {/if}
                    </button>
                  </form>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>
</section>

<style>
  .page-layout {
    display: flex;
    justify-content: center;
    padding-top: 4rem;
    padding-bottom: 4rem;
    min-height: 80vh;
  }

  .dashboard-card {
    background: #fff;
    width: 100%;
    max-width: 1000px;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    padding: 2rem;
    border: 1px solid #eaeaea;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid var(--background-color);
  }

  .header h1 {
    font-size: 24px;
    padding-top: 0;
    margin: 0;
    color: var(--primary-color);
  }

  .actions {
    display: flex;
    gap: 1rem;
    align-items: center;
  }

  .table-wrapper {
    overflow-x: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
  }

  th {
    text-align: left;
    font-size: 12px;
    font-family: var(--body-font);
    color: grey;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding-bottom: 12px;
    border-bottom: 1px solid #eee;
  }

  td {
    padding: 16px 0;
    border-bottom: 1px solid var(--background-color);
    vertical-align: middle;
  }

  tr:last-child td {
    border-bottom: none;
  }

  .file-cell {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 500;
    color: var(--text-color);
  }

  .filename {
    max-width: 250px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .media-id-cell {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .media-id-cell code {
    font-size: 12px;
    color: grey;
    background: var(--background-color);
    padding: 2px 6px;
    border-radius: 4px;
  }

  .copy-btn {
    background: none;
    border: none;
    cursor: pointer;
    color: grey;
    padding: 4px;
    display: flex;
    align-items: center;
    border-radius: 4px;
  }

  .copy-btn:hover {
    background: var(--background-color);
    color: var(--primary-color);
  }

  .badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .status-success {
    background-color: #d1fae5;
    color: #065f46;
  }

  .status-processing {
    background-color: #fff7ed;
    color: var(--secondary-color);
    border: 1px solid #ffedd5;
  }

  .status-error {
    background-color: #fef2f2;
    color: #b91c1c;
  }

  .icon-button {
    background: none;
    border: none;
    cursor: pointer;
    color: grey;
    padding: 8px;
    border-radius: 50%;
    transition: background-color 0.2s, color 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .icon-button:hover {
    background-color: var(--background-color);
    color: var(--text-color);
  }

  .delete-icon:hover {
    color: #ef4444;
    background-color: #fef2f2;
  }

  .state-container {
    padding: 4rem 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    text-align: center;
  }

  .error-banner {
    background-color: #fef2f2;
    color: #b91c1c;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 1rem;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .text-right { text-align: right; }

  .mobile-meta { display: none; margin-top: 4px; font-size: 11px; }

  @media (max-width: 640px) {
    .desktop-only { display: none; }
    .mobile-meta { display: block; }
    .dashboard-card { padding: 1rem; }
  }
</style>