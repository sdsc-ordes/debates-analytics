<script lang="ts">
  import { onMount } from 'svelte';
  import { Trash2, FileVideo, Loader, RefreshCw, AlertCircle, Upload } from 'lucide-svelte';

  type MediaItem = {
    media_id: string;
    filename: string;
    status: string;
    created_at: string;
    title?: string;
  };

  let items = $state<MediaItem[]>([]);
  let isLoading = $state(true);
  let error = $state<string | null>(null);
  let isDeleting = $state<string | null>(null);

  // 1. Fetch List
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

  // 2. Handle Delete
  async function handleDelete(mediaId: string) {
    if (!confirm('Are you sure? This will delete files from S3, Solr, and MongoDB.')) return;

    isDeleting = mediaId;
    try {
      const res = await fetch('/api/metadata/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mediaId })
      });
      if (!res.ok) throw new Error('Delete failed');
      items = items.filter(i => i.media_id !== mediaId);
    } catch (e: any) {
      alert(`Error deleting: ${e.message}`);
    } finally {
      isDeleting = null;
    }
  }

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

  onMount(() => {
    loadMedia();
  });
</script>

<svelte:head>
  <title>Dashboard</title>
</svelte:head>

<section class="page-layout">
  <div class="dashboard-card">
    
    <div class="header">
      <h1>Media Library</h1>
      <div class="actions">
        <button class="icon-button" onclick={loadMedia} title="Refresh List">
          <RefreshCw class={isLoading ? 'animate-spin' : ''} size={18} />
        </button>
        <a href="/" class="button-primary" style="text-decoration: none;">
          <Upload size={14} style="margin-right: 6px;" /> Upload New
        </a>
      </div>
    </div>

    {#if error}
      <div class="error-banner">
        <AlertCircle size={16} />
        <span>{error}</span>
      </div>
    {/if}

    {#if isLoading && items.length === 0}
      <div class="state-container">
        <Loader class="animate-spin" size={24} color="var(--primary-color)" />
        <p class="card-subtle">Loading library...</p>
      </div>

    {:else if items.length === 0}
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
                    <FileVideo size={16} color="var(--primary-color)" />
                    <span class="filename" title={item.media_id}>{item.filename} {item.media_id}</span>
                  </div>
                  <div class="mobile-meta card-subtle">{formatDate(item.created_at)}</div>
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
                  <button 
                    class="icon-button delete-icon" 
                    onclick={() => handleDelete(item.media_id)}
                    disabled={isDeleting === item.media_id}
                    title="Delete Media"
                  >
                    {#if isDeleting === item.media_id}
                      <Loader class="animate-spin" size={16} />
                    {:else}
                      <Trash2 size={16} />
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
  /* Layout centering matching your text-column approach */
  .page-layout {
    display: flex;
    justify-content: center;
    padding-top: 4rem; /* Matching your global vars */
    padding-bottom: 4rem;
    min-height: 80vh;
  }

  .dashboard-card {
    background: #fff;
    width: 100%;
    max-width: 1000px; /* Matching your CSS text-column width */
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05); /* Subtle shadow like the screenshot */
    padding: 2rem;
    border: 1px solid #eaeaea;
  }

  /* Header matches your h1 styles but adjusted for card context */
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
    padding-top: 0; /* Override global h1 padding */
    margin: 0;
    color: var(--primary-color); /* Branding */
  }

  .actions {
    display: flex;
    gap: 1rem;
    align-items: center;
  }

  /* Tables - Minimalist Style */
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

  /* Badges using your variables */
  .badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  /* Success: Greenish (Custom, or use Primary if you prefer blue) */
  .status-success {
    background-color: #d1fae5;
    color: #065f46;
  }

  /* Processing: Uses your Secondary Color (Orange) for visibility */
  .status-processing {
    background-color: #fff7ed;
    color: var(--secondary-color);
    border: 1px solid #ffedd5;
  }

  /* Error: Red */
  .status-error {
    background-color: #fef2f2;
    color: #b91c1c;
  }

  /* Buttons */
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
    color: #ef4444; /* Red on hover */
    background-color: #fef2f2;
  }

  /* States */
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

  /* Mobile Responsive */
  .mobile-meta { display: none; margin-top: 4px; font-size: 11px; }
  
  @media (max-width: 640px) {
    .desktop-only { display: none; }
    .mobile-meta { display: block; }
    .dashboard-card { padding: 1rem; }
  }
</style>