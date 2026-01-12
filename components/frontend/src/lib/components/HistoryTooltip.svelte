<script lang="ts">
  import { Clock } from 'lucide-svelte';

  // Define the type for a history item based on your data
  type HistoryItem = {
    step: string;
    timestamp: string;
  };

  let { history }: { history: HistoryItem[] } = $props();

  function formatTime(isoString: string) {
    if (!isoString) return '';
    return new Date(isoString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  }

  function formatStepName(step: string) {
    return step
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (l) => l.toUpperCase()); // Title Case
  }
</script>

<div class="history-tooltip">
  <div class="tooltip-header">
    <Clock size={14} class="text-muted" />
    <span>Processing History</span>
  </div>

  {#if !history || history.length === 0}
    <div class="empty-state">No history recorded</div>
  {:else}
    <div class="timeline">
      {#each history as event, i}
        <div class="timeline-item">
          <div class="timeline-marker">
            <div class="dot {i === history.length - 1 ? 'active' : ''}"></div>
            {#if i !== history.length - 1}
              <div class="line"></div>
            {/if}
          </div>

          <div class="timeline-content">
            <span class="step-name {i === history.length - 1 ? 'current' : ''}">
              {formatStepName(event.step)}
            </span>
            <span class="step-time">
              {formatTime(event.timestamp)}
            </span>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .history-tooltip {
    position: absolute;
    top: 100%;       /* Position right below the status badge */
    left: 50%;
    transform: translateX(-50%);
    margin-top: 8px; /* Small gap */
    width: 280px;
    background: white;
    border: 1px solid #e2e8f0;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    border-radius: 8px;
    padding: 12px;
    z-index: 50;     /* Ensure it sits on top of other table rows */
    pointer-events: none; /* Let clicks pass through, or set to auto if you want to select text */
    text-align: left;
  }

  /* Optional: Add a little arrow pointing up */
  .history-tooltip::before {
    content: '';
    position: absolute;
    top: -5px;
    left: 50%;
    transform: translateX(-50%) rotate(45deg);
    width: 10px;
    height: 10px;
    background: white;
    border-left: 1px solid #e2e8f0;
    border-top: 1px solid #e2e8f0;
  }

  .tooltip-header {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #64748b;
    margin-bottom: 12px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 1px solid #f1f5f9;
    padding-bottom: 8px;
  }

  .timeline {
    display: flex;
    flex-direction: column;
  }

  .timeline-item {
    display: flex;
    gap: 10px;
    position: relative;
    padding-bottom: 0; /* Removing padding bottom to let flex handle gap */
    min-height: 24px;
  }

  .timeline-marker {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 12px;
  }

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #cbd5e1;
    z-index: 2;
  }

  .dot.active {
    background-color: #3b82f6; /* Primary color for latest step */
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
  }

  .line {
    width: 2px;
    flex-grow: 1;
    background-color: #e2e8f0;
    margin-top: -2px; /* Pull line up to connect to dot center */
    margin-bottom: -2px;
    min-height: 16px;
  }

  .timeline-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-grow: 1;
    padding-bottom: 12px; /* Spacing between items */
  }

  .timeline-item:last-child .timeline-content {
    padding-bottom: 0;
  }

  .step-name {
    font-size: 0.8rem;
    color: #475569;
    font-weight: 500;
    line-height: 1;
  }

  .step-name.current {
    color: #1e293b;
    font-weight: 700;
  }

  .step-time {
    font-size: 0.7rem;
    color: #94a3b8;
    white-space: nowrap;
    margin-left: 8px;
    font-family: monospace;
  }

  .empty-state {
    font-size: 0.8rem;
    color: #94a3b8;
    text-align: center;
    padding: 8px 0;
  }
</style>
