<script lang="ts">
  import { displayIsoDate } from "$lib/utils/displayUtils";
  import type { components } from '$lib/api/schema';
  type DebateDocument = components['schemas']['DebateDocument'];

  interface Props {
    debate: DebateDocument;
  }

  let { debate }: Props = $props();
  console.log("debate", debate)

  const get_debate_title = () => {
      if (debate.session && debate.type) {
          return `${debate.session} ${debate.type}`
      } else if (debate.session) {
          return debate.session
      } else {
          return debate.media_id
      }
  }
</script>

<div class="card-title-large" style="color: var(--primary-dark-color);">
  {get_debate_title()}
  {#if debate.schedule}
  <div class="date-time-item">
    <!-- <i class="fa fa-calendar" aria-hidden="true"></i> -->
    <div class="card-title-small">{displayIsoDate(debate.schedule)}</div>
  </div>
  {/if}
</div>
