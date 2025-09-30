<script lang="ts">
import { onMount } from 'svelte';
import { getWorkouts } from '$lib/data/workouts';
let workouts = [];
let chartData = [];
let chartLabels = [];
let isLoading = true;
let error: string | null = null;

onMount(async () => {
  try {
    isLoading = true;
    error = null;
    workouts = await getWorkouts();
    console.log(workouts);
    // Example: Use workout scheduledDate or createdAt for x-axis, and grade from name (e.g. V5, V6, 5.12a) for y-axis
    chartData = workouts.map((w: any) => {
      // Extract grade from name (simple regex for V-grade or YDS)
      const match = w.name.match(/(V\d+|5\.\d+[abcd]?)/);
      return match ? match[0] : null;
    });
    chartLabels = workouts.map((w: any) => (w.scheduledDate ? w.scheduledDate.slice(0, 10) : w.createdAt.slice(0, 10)));
  } catch (err) {
    error = 'Failed to load progress data.';
  } finally {
    isLoading = false;
  }
});

function gradeToNumber(grade: string | null): number {
  if (!grade) return 0;
  if (grade.startsWith('V')) return parseInt(grade.slice(1));
  if (grade.startsWith('5.')) {
    // Convert YDS to a number (e.g. 5.10a -> 10, 5.12d -> 12)
    const num = parseInt(grade.slice(2));
    return isNaN(num) ? 0 : num;
  }
  return 0;
}
</script>

{#if isLoading}
  <div>Loading progress chart...</div>
{:else if error}
  <div class="error-message">{error}</div>
{:else}
  <div class="progress-chart">
    <h3>Max Grade Over Time</h3>
    <div class="svg-wrapper">
      <svg width="100%" height="220" viewBox="0 0 420 220">
        {#if chartData.length > 1}
          {#each chartData as grade, i}
            {#if i > 0}
              <line
                x1={(i - 1) * (400 / (chartData.length - 1)) + 10}
                y1={200 - gradeToNumber(chartData[i - 1]) * 15}
                x2={i * (400 / (chartData.length - 1)) + 10}
                y2={200 - gradeToNumber(grade) * 15}
                stroke="#3182ce"
                stroke-width="2"
              />
            {/if}
          {/each}
          {#each chartData as grade, i}
            <circle
              cx={i * (400 / (chartData.length - 1)) + 10}
              cy={200 - gradeToNumber(grade) * 15}
              r="5"
              fill="#3182ce"
            />
            <text
              x={i * (400 / (chartData.length - 1)) + 10}
              y="215"
              font-size="12"
              fill="#666"
              text-anchor="middle"
              transform={`rotate(-45,${i * (400 / (chartData.length - 1)) + 10},215)`}
            >{chartLabels[i]}</text>
          {/each}
        {:else}
          <text x="20" y="100" fill="#888">Not enough data to show chart</text>
        {/if}
      </svg>
    </div>
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
  max-width: 700px;
  margin-left: auto;
  margin-right: auto;
}
.svg-wrapper {
  width: 100%;
  overflow-x: auto;
  padding-bottom: 1rem;
}
</style>
