<script lang="ts">
  import type { Debate } from "$lib/interfaces/metadata.interface";
  import { displayIsoDate } from "$lib/utils/displayUtils";

  interface Props {
    debate: Debate;
  }

  let { debate }: Props = $props();
</script>

<div class="card-title-large" style="color: var(--primary-dark-color);">
  {debate.media}
  <div class="date-time-item">
    <div class="card-title-small">{debate.job_id}</div>
  </div>
</div>
