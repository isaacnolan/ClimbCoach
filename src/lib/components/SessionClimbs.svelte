<script lang="ts">
  import { onMount } from 'svelte';
  export let sessionDate: string;
  let climbs: any[] = [];
  let loading = true;
  let error: string | null = null;

  // Attempt to fetch session by date; API may need an ID in future. We'll query training sessions and find by date as a best-effort.
  import { getTrainingSessions } from '$lib/data/trainingSessions';

  onMount(async () => {
    try {
      loading = true;
      const to = new Date(sessionDate);
      const from = new Date(sessionDate);
      from.setDate(from.getDate() - 1);
      to.setDate(to.getDate() + 1);
      const data = await getTrainingSessions({ from: from.toISOString(), to: to.toISOString() });
      // find session with matching date
      const found = (data || []).find((s: any) => new Date(s.scheduledDate).toDateString() === new Date(sessionDate).toDateString());
      climbs = found ? (found.climbs || []) : [];
    } catch (e) {
      error = 'Failed to load climbs';
    } finally {
      loading = false;
    }
  });
</script>

{#if loading}
  <div>Loading climbs…</div>
{:else if error}
  <div class="error">{error}</div>
{:else}
  {#if climbs.length === 0}
    <div>No climbs recorded for this session.</div>
  {:else}
    <table style="width:100%;border-collapse:collapse">
      <thead>
        <tr>
          <th style="text-align:left;padding:6px;border-bottom:1px solid #eee">Name</th>
          <th style="text-align:left;padding:6px;border-bottom:1px solid #eee">Grade</th>
          <th style="text-align:right;padding:6px;border-bottom:1px solid #eee">Attempts</th>
        </tr>
      </thead>
      <tbody>
        {#each climbs as c}
          <tr>
            <td style="padding:6px;border-bottom:1px solid #fafafa">{c.name}</td>
            <td style="padding:6px;border-bottom:1px solid #fafafa">{c.grade}</td>
            <td style="padding:6px;text-align:right;border-bottom:1px solid #fafafa">{c.attempts ?? 1}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  {/if}
{/if}

<style>
.error { color: #e74c3c }
</style>
