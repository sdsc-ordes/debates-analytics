<script lang="ts">
  import { onMount } from 'svelte';
  import { Trash2, FileVideo, Loader, RefreshCw, AlertCircle } from 'lucide-svelte';

  // 1. Type Definition matching your Python 'MediaListItem'
  type MediaItem = {
    media_id: string;
    filename: string;
    status: string;
    created_at: string;
    title?: string;
  };

  // 2. State
  let items = $state<MediaItem[]>([]);
  $inspect(items);
  let isLoading = $state(true);
  let error = $state<string | null>(null);
  let isDeleting = $state<string | null>(null); // Stores the ID currently being deleted

  // 3. Fetch List
  async function loadMedia() {
    isLoading = true;
    error = null;
    try {
      const res = await fetch('/api/metadata/list');
      if (!res.ok) throw new Error(`Failed to load: ${res.statusText}`);

      const data = await res.json();
      items = data.items.sort((a: MediaItem, b: MediaItem) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
    } catch (e: any) {
      error = e.message;
    } finally {
      isLoading = false;
    }
  }

  // 4. Handle Delete
  async function handleDelete(mediaId: string) {
    if (!confirm('Are you sure? This will delete files from S3, Solr, and MongoDB.')) return;

    isDeleting = mediaId;
    try {
      // Calls DELETE http://backend:8000/metadata/{id} via proxy
      const res = await fetch(`/api/metadata/${mediaId}`, {
        method: 'DELETE'
      });

      if (!res.ok) throw new Error('Delete failed');

      // Optimistic UI update: Remove from list immediately
      items = items.filter(i => i.media_id !== mediaId);
    } catch (e: any) {
      alert(`Error deleting: ${e.message}`);
    } finally {
      isDeleting = null;
    }
  }

  // 5. Format Helpers
  function formatDate(isoString: string) {
    return new Date(isoString).toLocaleString('en-US', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  }

  function getStatusColor(status: string) {
    if (status.includes('completed') || status === 'success') return 'badge-success';
    if (status.includes('failed') || status.includes('error')) return 'badge-error';
    if (status === 'queued' || status === 'idle') return 'badge-gray';
    return 'badge-processing'; // Default for transcribing, downloading, etc.
  }

  onMount(() => {
    loadMedia();
  });
</script>

<svelte:head>
  <title>Media Dashboard</title>
</svelte:head>

<section class="page-container">
  <div class="card">

    <div class="header">
      <h1>Media Library</h1>
      <button class="icon-btn" onclick={loadMedia} title="Refresh">
        <RefreshCw class={isLoading ? 'animate-spin' : ''} size={20} />
      </button>
    </div>

    {#if error}
      <div class="error-banner">
        <AlertCircle size={18} />
        <span>{error}</span>
      </div>
    {/if}

    {#if isLoading && items.length === 0}
      <div class="loading-state">
        <Loader class="animate-spin text-blue-500" size={32} />
        <p>Loading library...</p>
      </div>

    {:else if items.length === 0}
      <div class="empty-state">
        <FileVideo size={48} class="text-gray-300" />
        <p>No media found.</p>
        <a href="/" class="btn-primary">Upload Video</a>
      </div>

    {:else}
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>File</th>
              <th>Status</th>
              <th>Uploaded</th>
              <th class="text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {#each items as item (item.media_id)}
              <tr>
                <td>
                  <div class="file-info">
                    <FileVideo size={18} class="text-gray-400" />
                    <span class="filename" title={item.media_id}>{item.filename}</span>
                  </div>
                  <div class="mobile-meta">{formatDate(item.created_at)}</div>
                </td>

                <td>
                  <span class="badge {getStatusColor(item.status)}">
                    {item.status.replace(/_/g, ' ')}
                  </span>
                </td>

                <td class="desktop-only">
                  {formatDate(item.created_at)}
                </td>

                <td class="text-right">
                  <button
                    class="delete-btn"
                    onclick={() => handleDelete(item.media_id)}
                    disabled={isDeleting === item.media_id}
                    title="Delete"
                  >
                    {#if isDeleting === item.media_id}
                      <Loader class="animate-spin" size={18} />
                    {:else}
                      <Trash2 size={18} />
                    {/if}
                  </button>
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
  /* Layout */
  .page-container {
    display: flex;
    justify-content: center;
    padding: 2rem 1rem;
    background-color: #f9fafb;
    min-height: 100vh;
  }

  .card {
    background: white;
    width: 100%;
    max-width: 64rem; /* Wide */
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    border: 1px solid #e5e7eb;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  /* Header */
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid #f3f4f6;
  }
  h1 { font-size: 1.25rem; font-weight: 600; color: #111827; margin: 0; }
  
  /* Buttons */
  .icon-btn {
    background: none; border: none; cursor: pointer; color: #6b7280; padding: 0.5rem;
    border-radius: 50%; transition: background 0.2s;
  }
  .icon-btn:hover { background: #f3f4f6; color: #111827; }

  .delete-btn {
    background: none; border: none; cursor: pointer; color: #ef4444; padding: 0.5rem;
    border-radius: 6px; transition: background 0.2s;
  }
  .delete-btn:hover { background: #fef2f2; }
  .delete-btn:disabled { opacity: 0.5; cursor: not-allowed; }

  .btn-primary {
    display: inline-block; background: #3b82f6; color: white; padding: 0.75rem 1.5rem;
    border-radius: 6px; text-decoration: none; font-weight: 500; margin-top: 1rem;
  }

  /* States */
  .loading-state, .empty-state {
    padding: 4rem; display: flex; flex-direction: column; align-items: center; gap: 1rem; color: #6b7280;
  }
  .error-banner {
    background: #fef2f2; color: #b91c1c; padding: 1rem; margin: 1rem; border-radius: 6px;
    display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem;
  }

  /* Table */
  .table-container { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; text-align: left; }
  th { 
    background: #f9fafb; font-weight: 500; color: #6b7280; font-size: 0.75rem; 
    text-transform: uppercase; letter-spacing: 0.05em; padding: 0.75rem 1.5rem;
  }
  td { padding: 1rem 1.5rem; border-bottom: 1px solid #f3f4f6; vertical-align: middle; color: #374151; }
  tr:last-child td { border-bottom: none; }
  
  .file-info { display: flex; align-items: center; gap: 0.75rem; font-weight: 500; color: #111827; }
  .filename { max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

  /* Badges */
  .badge {
    display: inline-flex; align-items: center; padding: 0.25rem 0.75rem; 
    border-radius: 9999px; font-size: 0.75rem; font-weight: 500; text-transform: capitalize;
  }
  .badge-success { background: #d1fae5; color: #065f46; } /* Green */
  .badge-processing { background: #dbeafe; color: #1e40af; } /* Blue */
  .badge-error { background: #fee2e2; color: #991b1b; } /* Red */
  .badge-gray { background: #f3f4f6; color: #374151; } /* Gray */

  .text-right { text-align: right; }

  /* Responsive */
  .mobile-meta { display: none; font-size: 0.75rem; color: #9ca3af; margin-top: 0.25rem; }
  @media (max-width: 640px) {
    .desktop-only { display: none; }
    .mobile-meta { display: block; }
    th, td { padding: 1rem; }
  }
</style>