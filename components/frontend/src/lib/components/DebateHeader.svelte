<script lang="ts">
  import type { Debate } from "$lib/interfaces/metadata.interface";
  import { displayIsoDate } from "$lib/utils/displayUtils";

  export let debate: Debate;
</script>

<div class="card-title-large" style="color: var(--primary-dark-color);">
  {debate.media}
  <div class="date-time-item">
    <div class="card-title-small">{debate.job_id}</div>
  </div>
</div>
