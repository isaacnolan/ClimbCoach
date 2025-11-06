<script lang="ts">
import { onMount } from 'svelte';
import { getTrainingSessions } from '$lib/data/trainingSessions';
import { computeSessionLoads, computeACWR } from '$lib/load';
import ChartSVG from '$lib/components/ChartSVG.svelte';
import ACWRChart from '$lib/components/ACWRChart.svelte';
import SessionClimbs from '$lib/components/SessionClimbs.svelte';

let isLoading = true;
let isLoadingSessions = false;
let error: string | null = null;
let sessionsError: string | null = null;

// Training load state
let sessionLoads: { scheduledDate: string; name: string; load: number }[] = [];
let acwrResult: { ewma7: number | null; ewma42: number | null; acwr: number | null } | null = null;
let acwrSeries: { ewma7Series?: number[]; ewma42Series?: number[] } | null = null;
let gMaxOverride: number | '' = '';
let weights = { boulder: 1.0, sport: 0.75, other: 0.8 };
let timeWeighted = false;
let expandedSessionId: number | null = null; // use index to expand per-session climbs

function formatDate(iso?: string) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return d.toLocaleDateString();
  } catch (e) {
    return iso;
  }
}

async function loadAndCompute() {
  try {
    isLoadingSessions = true;
    sessionsError = null;
    const to = new Date();
    const from = new Date();
    from.setDate(to.getDate() - 180);
    const data = await getTrainingSessions({ from: from.toISOString(), to: to.toISOString() });

    const gMax = gMaxOverride === '' ? undefined : Number(gMaxOverride);
    const { sessions, gMax: inferred } = computeSessionLoads(data || [], gMax, weights);
    sessionLoads = sessions;
    const acwr = computeACWR(sessions.map(s => ({ scheduledDate: s.scheduledDate, load: s.load })), { timeWeighted });
    acwrResult = { ewma7: acwr.ewma7 ?? null, ewma42: acwr.ewma42 ?? null, acwr: acwr.acwr ?? null };
    acwrSeries = { ewma7Series: acwr.ewma7Series, ewma42Series: acwr.ewma42Series };
  } catch (err) {
    console.error('Failed to load sessions', err);
    sessionsError = 'Failed to load training sessions';
  } finally {
    isLoadingSessions = false;
    isLoading = false;
  }
}

onMount(() => {
  loadAndCompute();
});

$: if (gMaxOverride !== '') {
  loadAndCompute();
}

$: if (weights || timeWeighted) {
  loadAndCompute();
}
</script>

{#if isLoading}
  <div>Loading progress chart...</div>
{:else}
  <div class="progress-chart">
    <h2>Training Load & Progress</h2>

    {#if isLoadingSessions}
      <div>Loading sessions...</div>
    {:else}
      {#if sessionsError}
        <div class="error">{sessionsError}</div>
      {:else}
        {#if sessionLoads.length === 0}
          <div>No training sessions found.</div>
        {:else}
          <div>
            {#if sessionLoads.length > 0 && acwrSeries}
              <div style="margin-top:1rem">
                <ChartSVG {sessionLoads} {acwrSeries} />
              </div>
              <div style="margin-top:0.75rem">
                <ACWRChart {sessionLoads} {acwrSeries} />
              </div>
            {:else}
              <div>Not enough data to show charts.</div>
            {/if}
          </div>
        {/if}
      {/if}
    {/if}
  </div>
{/if}

<style>
.progress-chart {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.08);
  padding: 2rem;
  margin-bottom: 2rem;
  min-width: 350px;
  max-width: 980px;
  margin-left: auto;
  margin-right: auto;
}

input, select, textarea {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.error { color: #e74c3c; }
</style>
