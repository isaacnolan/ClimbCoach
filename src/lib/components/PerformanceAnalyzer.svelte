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

      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          userId: 'user-1', // TODO: Replace with actual user ID
          performance
        })
      });

      const data = await response.json();

      if (data.success) {
        analysis = data.analysis;
      } else {
        error = data.error;
      }
    } catch (err) {
      console.error('Error analyzing performance:', err);
      error = 'Failed to analyze performance';
    } finally {
      isLoading = false;
    }
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
    <div class="error">
      {error}
    </div>
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
  .analyzer {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
  }

  .form-group {
    margin-bottom: 1rem;
  }

  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
  }

  input, select, textarea {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
  }

  textarea {
    min-height: 100px;
    resize: vertical;
  }

  button {
    background: #3498db;
    color: white;
    border: none;
    padding: 0.8rem 1.5rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    width: 100%;
  }

  button:disabled {
    background: #ccc;
    cursor: not-allowed;
  }

  .error {
    color: #e74c3c;
    padding: 1rem;
    background: #fee;
    border-radius: 4px;
    margin: 1rem 0;
  }

  .analysis {
    margin-top: 2rem;
    padding: 1rem;
    background: #f8f9fa;
    border-radius: 4px;
  }

  .analysis h3 {
    margin-top: 1.5rem;
    color: #2c3e50;
  }

  .analysis ul {
    list-style-type: none;
    padding: 0;
  }

  .analysis li {
    padding: 0.5rem 0;
    border-bottom: 1px solid #eee;
  }

  .analysis li:last-child {
    border-bottom: none;
  }
</style> 