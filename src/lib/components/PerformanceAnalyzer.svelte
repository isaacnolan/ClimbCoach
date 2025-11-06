<script lang="ts">
  import { onMount } from 'svelte';
  import type { ClimbingPerformance, ChainOfThought } from '$lib/ai/types';

  let performance: ClimbingPerformance = {
    grade: 'V4',
    style: 'boulder',
    completion: 'redpoint',
    attempts: 3,
    notes: 'Struggled with the crux move'
  };

  let analysis: ChainOfThought | null = null;
  let isLoading = false;
  let error: string | null = null;

  async function analyzePerformance() {
    try {
      isLoading = true;
      error = null;
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: 'user-1', performance })
      });
      const data = await res.json();
      if (data.success) analysis = data.analysis;
      else error = data.error || 'Analysis failed';
    } catch (e) {
      console.error(e);
      error = 'Failed to analyze performance';
    } finally {
      isLoading = false;
    }
  }

  function formatDate(iso?: string) {
    if (!iso) return '';
    try { return new Date(iso).toLocaleDateString(); } catch { return iso; }
  }
</script>

<div class="analyzer">
  <h2>Performance Analysis</h2>

  <div class="form-group">
    <label for="grade">Grade</label>
    <input type="text" id="grade" bind:value={performance.grade} />
  </div>

  <div class="form-group">
    <label for="style">Style</label>
    <select id="style" bind:value={performance.style}>
      <option value="boulder">Boulder</option>
      <option value="sport">Sport</option>
      <option value="trad">Trad</option>
    </select>
  </div>

  <div class="form-group">
    <label for="completion">Completion</label>
    <select id="completion" bind:value={performance.completion}>
      <option value="flash">Flash</option>
      <option value="onsight">Onsight</option>
      <option value="redpoint">Redpoint</option>
      <option value="failed">Failed</option>
    </select>
  </div>

  <div class="form-group">
    <label for="attempts">Attempts</label>
    <input type="number" id="attempts" bind:value={performance.attempts} min="1" />
  </div>

  <div class="form-group">
    <label for="notes">Notes</label>
    <textarea id="notes" bind:value={performance.notes}></textarea>
  </div>

  <button on:click={analyzePerformance} disabled={isLoading}>
    {isLoading ? 'Analyzing...' : 'Analyze Performance'}
  </button>

  {#if error}
    <div class="error">{error}</div>
  {/if}

  {#if analysis}
    <div class="analysis">
      <h3>Observations</h3>
      <ul>
        {#each analysis.observations as observation}
          <li>{observation}</li>
        {/each}
      </ul>

      <h3>Analysis</h3>
      <ul>
        {#each analysis.analysis as item}
          <li>{item}</li>
        {/each}
      </ul>

      <h3>Conclusions</h3>
      <ul>
        {#each analysis.conclusions as conclusion}
          <li>{conclusion}</li>
        {/each}
      </ul>

      <h3>Recommendations</h3>
      <ul>
        {#each analysis.recommendations as recommendation}
          <li>{recommendation}</li>
        {/each}
      </ul>
    </div>
  {/if}
</div>

<style>
  .analyzer { max-width: 800px; margin: 0 auto; padding: 2rem; }
  .form-group { margin-bottom: 1rem; }
  label { display:block; margin-bottom:0.5rem; font-weight:500; }
  input, select, textarea { width:100%; padding:0.5rem; border:1px solid #ddd; border-radius:4px }
  textarea { min-height:100px }
  button { background:#3498db; color:white; border:none; padding:0.8rem 1.5rem; border-radius:4px; cursor:pointer }
  .error { color:#e74c3c; padding:0.75rem; background:#fff6f6; border-radius:6px; margin-top:1rem }
  .analysis { margin-top:1.25rem; background:#f8f9fa; padding:1rem; border-radius:6px }
</style>