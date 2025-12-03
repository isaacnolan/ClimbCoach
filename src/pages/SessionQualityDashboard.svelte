<script lang="ts">
  import { onMount } from 'svelte';
  import { getTrainingSessions } from '$lib/data/trainingSessions';
  import {
    computeSessionQualities,
    qualityRating,
    type TrainingSessionForQuality,
    type SessionQualityBreakdown,
    type AggregatedQuality
  } from '$lib/sessionQuality';

  let isLoading = true;
  let error: string | null = null;

  let allSessionsRaw: TrainingSessionForQuality[] = [];
  let allSessionsScored: SessionQualityBreakdown[] = [];
  let aggregatedSelected: AggregatedQuality | null = null;

  // filters / selection
  let searchText = '';
  let fromDate: string = '';
  let toDate: string = '';
  let selectedWorkoutId: string = 'all';

  let selectedIds = new Set<string>();

  let filteredSessions: SessionQualityBreakdown[] = [];
  let selectedSessions: SessionQualityBreakdown[] = [];

  let workoutOptions: { id: string; name: string }[] = [];

  // Derived points for the SVG trend line
  $: trendPoints =
    aggregatedSelected && aggregatedSelected.scoreSeries.length > 1
      ? aggregatedSelected.scoreSeries.map((p, i, arr) => {
          const maxIndex = Math.max(1, arr.length - 1);
          const x = (i / maxIndex) * 380 + 10;
          const y = 130 - (p.score / 100) * 110;
          return { x, y };
        })
      : [];

  const fmtDateTime = (iso: string) =>
    new Date(iso).toLocaleString();

  const fmtDate = (iso: string) =>
    new Date(iso).toLocaleDateString();

  async function loadSessions() {
    try {
      isLoading = true;
      error = null;

      const sessions = await getTrainingSessions();
      // cast into our enriched type; this is compatible with your +page.svelte type
      allSessionsRaw = sessions.map((s: any) => ({
        id: s.id,
        name: s.name,
        scheduledDate: s.scheduledDate,
        description: s.description ?? null,
        workout: s.workout ?? null,
        climbs: s.climbs ?? []
      })) as TrainingSessionForQuality[];

      const { perSession, aggregated } = computeSessionQualities(allSessionsRaw);
      allSessionsScored = perSession;

      // initially, use all sessions as selected set
      selectedIds = new Set(allSessionsScored.map((s) => s.sessionId));

      // build workout filter options
      const wMap = new Map<string, string>();
      for (const s of allSessionsRaw) {
        if (s.workout?.id) {
          wMap.set(s.workout.id, s.workout.name ?? 'Untitled workout');
        }
      }
      workoutOptions = Array.from(wMap.entries()).map(([id, name]) => ({ id, name }));

      recomputeFilteredAndSelected();
    } catch (e: any) {
      console.error(e);
      error = e?.message ?? 'Failed to load sessions.';
    } finally {
      isLoading = false;
    }
  }

    function recomputeFilteredAndSelected() {
    const fromTs = fromDate ? new Date(fromDate).getTime() : null;
    const toTs = toDate ? new Date(toDate).getTime() : null;

    // 1) Filter list
    filteredSessions = allSessionsScored.filter((s) => {
      const t = new Date(s.scheduledDate).getTime();
      if (fromTs != null && t < fromTs) return false;
      if (toTs != null && t > toTs) return false;

      if (selectedWorkoutId !== 'all') {
        const raw = allSessionsRaw.find((r) => r.id === s.sessionId);
        if (!raw || raw.workout?.id !== selectedWorkoutId) return false;
      }

      if (searchText.trim()) {
        const q = searchText.trim().toLowerCase();
        if (
          !s.name.toLowerCase().includes(q) &&
          !(s.workoutName ?? '').toLowerCase().includes(q)
        ) {
          return false;
        }
      }

      return true;
    });

    const base = filteredSessions.length ? filteredSessions : allSessionsScored;
    const selectedList = base.filter((s) => selectedIds.has(s.sessionId));

    // if user cleared everything, default to "all in filtered list"
    selectedSessions = selectedList.length ? selectedList : base;

    // 2) Build aggregatedSelected directly from selectedSessions
    if (selectedSessions.length) {
      const n = selectedSessions.length;
      const sum = (fn: (x: SessionQualityBreakdown) => number) =>
        selectedSessions.reduce((acc, s) => acc + fn(s), 0);

      aggregatedSelected = {
        sessionsCount: n,
        averageScore: sum((s) => s.score) / n,
        avgVolumeScore: sum((s) => s.volumeScore) / n,
        avgDifficultyScore: sum((s) => s.difficultyScore) / n,
        avgConsistencyScore: sum((s) => s.consistencyScore) / n,
        avgIntensityScore: sum((s) => s.intensityScore) / n,
        avgProgressScore: sum((s) => s.progressScore) / n,
        scoreSeries: selectedSessions
          .map((s) => ({
            date: new Date(s.scheduledDate),
            score: s.score,
            name: s.name,
          }))
          .sort((a, b) => a.date.getTime() - b.date.getTime()),
      };
    } else {
      aggregatedSelected = null;
    }
  }


  function toggleSessionSelection(id: string) {
    if (selectedIds.has(id)) {
      selectedIds.delete(id);
    } else {
      selectedIds.add(id);
    }
    selectedIds = new Set(selectedIds);
    recomputeFilteredAndSelected();
  }

  function selectAllFiltered() {
    for (const s of filteredSessions) {
      selectedIds.add(s.sessionId);
    }
    selectedIds = new Set(selectedIds);
    recomputeFilteredAndSelected();
  }

  function clearSelection() {
    selectedIds = new Set();
    recomputeFilteredAndSelected();
  }

  // recompute when filters change (once initial load is done)
  $: if (!isLoading && allSessionsScored.length) {
    recomputeFilteredAndSelected();
  }

  onMount(() => {
    loadSessions();
  });
</script>

<div class="sq-root">
  <p class="sub">
    Select training sessions to see a combined quality score, trends, and breakdown.
  </p>

  {#if isLoading}
    <div class="panel">Loading session quality…</div>
  {:else if error}
    <div class="panel error">
      {error}
    </div>
  {:else if !allSessionsScored.length}
    <div class="panel">
      No training sessions yet. Create a session to see quality analytics.
    </div>
  {:else}
    <!-- Filters row -->
    <div class="filters">
      <div>
        <label>Search</label>
        <input
          placeholder="Search by session or workout name"
          bind:value={searchText}
        />
      </div>
      <div>
        <label>From</label>
        <input type="date" bind:value={fromDate} />
      </div>
      <div>
        <label>To</label>
        <input type="date" bind:value={toDate} />
      </div>
      <div>
        <label>Workout</label>
        <select bind:value={selectedWorkoutId}>
          <option value="all">All workouts</option>
          {#each workoutOptions as w}
            <option value={w.id}>{w.name}</option>
          {/each}
        </select>
      </div>
    </div>

    <div class="layout">
      <!-- LEFT: selection list -->
      <div class="left-panel">
        <div class="left-header">
          <div>
            <strong>Sessions</strong>
            <div class="muted">
              {filteredSessions.length} shown · {selectedSessions.length} selected
            </div>
          </div>
          <div class="left-actions">
            <button type="button" on:click={selectAllFiltered}>Select all</button>
            <button type="button" on:click={clearSelection}>Clear</button>
          </div>
        </div>
        <div class="session-list">
          {#each filteredSessions as s}
            <label class="session-row">
              <input
                type="checkbox"
                checked={selectedIds.has(s.sessionId)}
                on:change={() => toggleSessionSelection(s.sessionId)}
              />
              <div class="session-row-main">
                <div class="row-top">
                  <span class="name">{s.name}</span>
                  <span class="score">{s.score.toFixed(0)}</span>
                </div>
                <div class="row-bottom">
                  <span>{fmtDate(s.scheduledDate)}</span>
                  {#if s.workoutName}
                    <span>· {s.workoutName}</span>
                  {/if}
                </div>
              </div>
            </label>
          {/each}
        </div>
      </div>

      <!-- RIGHT: combined analytics -->
      <div class="right-panel">
        <div class="summary-cards">
          <div class="card">
            <div class="label">Combined quality score</div>
            <div class="score-big">
              {#if aggregatedSelected}
                {aggregatedSelected.averageScore?.toFixed(1)}
              {:else}
                –
              {/if}
            </div>
            <div class="rating">
              {qualityRating(aggregatedSelected?.averageScore ?? null)}
            </div>
            <div class="meta">
              {selectedSessions.length} session{selectedSessions.length === 1 ? '' : 's'} selected
            </div>
          </div>

          {#if aggregatedSelected}
            <div class="card breakdown">
              <div class="label">Average components</div>
              <div class="breakdown-grid">
                <div>
                  <span>Volume</span>
                  <strong>{aggregatedSelected.avgVolumeScore.toFixed(1)}/20</strong>
                </div>
                <div>
                  <span>Difficulty</span>
                  <strong>{aggregatedSelected.avgDifficultyScore.toFixed(1)}/25</strong>
                </div>
                <div>
                  <span>Consistency</span>
                  <strong>{aggregatedSelected.avgConsistencyScore.toFixed(1)}/20</strong>
                </div>
                <div>
                  <span>Intensity</span>
                  <strong>{aggregatedSelected.avgIntensityScore.toFixed(1)}/15</strong>
                </div>
                <div>
                  <span>Progress</span>
                  <strong>{aggregatedSelected.avgProgressScore.toFixed(1)}/20</strong>
                </div>
              </div>
            </div>
          {/if}
        </div>

        <!-- Simple inline trend chart -->
        {#if trendPoints.length > 1}
          <div class="card">
            <div class="label">Score trend</div>
            <div class="chart-wrapper">
              <svg viewBox="0 0 400 140" class="sq-chart">
                <polyline
                  fill="none"
                  stroke="#2563eb"
                  stroke-width="2"
                  points={trendPoints.map((p) => `${p.x},${p.y}`).join(' ')}
                />
                {#each trendPoints as p}
                  <circle cx={p.x} cy={p.y} r="3" fill="#2563eb" />
                {/each}
              </svg>
            </div>
          </div>
        {/if}

        <!-- Per-session cards -->
        <div class="card session-cards">
          <div class="label">Selected sessions</div>
          {#if !selectedSessions.length}
            <p class="muted">No sessions selected.</p>
          {:else}
            <div class="cards-grid">
              {#each selectedSessions as s}
                <div class="session-card">
                  <div class="header-row">
                    <div>
                      <div class="name">{s.name}</div>
                      <div class="muted">
                        {fmtDateTime(s.scheduledDate)}
                        {#if s.workoutName}
                          · {s.workoutName}
                        {/if}
                      </div>
                    </div>
                    <div class="score-pill">
                      {s.score.toFixed(0)}
                    </div>
                  </div>
                  <div class="components">
                    <div><span>Volume</span><strong>{s.volumeScore.toFixed(1)}</strong></div>
                    <div><span>Diff.</span><strong>{s.difficultyScore.toFixed(1)}</strong></div>
                    <div><span>Consist.</span><strong>{s.consistencyScore.toFixed(1)}</strong></div>
                    <div><span>Intens.</span><strong>{s.intensityScore.toFixed(1)}</strong></div>
                    <div><span>Progress</span><strong>{s.progressScore.toFixed(1)}</strong></div>
                  </div>
                  <div class="small-meta">
                    <span>{s.totalClimbs} climbs</span>
                    <span>· {s.totalAttempts} attempts</span>
                    {#if s.avgGrade != null}
                      <span>· avg grade {s.avgGrade.toFixed(1)}</span>
                    {/if}
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .sq-root {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  h2 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
  }
  .sub {
    margin: 0 0 0.75rem;
    color: #6b7280;
    font-size: 0.9rem;
  }
  .panel {
    border-radius: 12px;
    padding: 1rem;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    font-size: 0.95rem;
  }
  .panel.error {
    background: #fef2f2;
    border-color: #fecaca;
    color: #b91c1c;
  }

  .filters {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.75rem;
    margin-bottom: 0.75rem;
  }
  .filters label {
    display: block;
    font-size: 0.8rem;
    margin-bottom: 0.25rem;
    color: #4b5563;
  }
  .filters input,
  .filters select {
    width: 100%;
    border-radius: 8px;
    border: 1px solid #d1d5db;
    padding: 0.35rem 0.5rem;
    font-size: 0.9rem;
  }

  .layout {
    display: grid;
    grid-template-columns: minmax(220px, 260px) minmax(0, 1fr);
    gap: 1rem;
    align-items: flex-start;
  }

  .left-panel {
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    background: #ffffff;
    display: flex;
    flex-direction: column;
    max-height: 480px;
  }
  .left-header {
    display: flex;
    justify-content: space-between;
    padding: 0.75rem 0.75rem 0.5rem;
    border-bottom: 1px solid #e5e7eb;
    gap: 0.75rem;
  }
  .left-actions {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  .left-actions button {
    font-size: 0.75rem;
    padding: 0.15rem 0.4rem;
    border-radius: 999px;
    border: 1px solid #d1d5db;
    background: #f9fafb;
    cursor: pointer;
  }
  .left-actions button:hover {
    background: #e5e7eb;
  }
  .muted {
    color: #6b7280;
    font-size: 0.8rem;
  }
  .session-list {
    overflow-y: auto;
    padding: 0.25rem 0.75rem 0.75rem;
  }
  .session-row {
    display: flex;
    gap: 0.5rem;
    align-items: flex-start;
    padding: 0.35rem 0;
    font-size: 0.85rem;
    cursor: pointer;
  }
  .session-row input {
    margin-top: 0.3rem;
  }
  .session-row-main {
    flex: 1;
  }
  .row-top {
    display: flex;
    justify-content: space-between;
    gap: 0.5rem;
  }
  .row-top .name {
    font-weight: 500;
    color: #111827;
  }
  .row-top .score {
    font-weight: 600;
    color: #2563eb;
  }
  .row-bottom {
    font-size: 0.78rem;
    color: #6b7280;
  }

  .right-panel {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  .summary-cards {
    display: grid;
    grid-template-columns: minmax(0, 1.1fr) minmax(0, 1.4fr);
    gap: 0.75rem;
  }
  .card {
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    background: #ffffff;
    padding: 0.75rem 0.9rem;
  }
  .label {
    font-size: 0.8rem;
    font-weight: 500;
    color: #6b7280;
    margin-bottom: 0.25rem;
  }
  .score-big {
    font-size: 2rem;
    font-weight: 700;
    color: #111827;
  }
  .rating {
    font-size: 0.9rem;
    color: #111827;
    margin-top: 0.1rem;
  }
  .meta {
    font-size: 0.8rem;
    color: #6b7280;
    margin-top: 0.15rem;
  }

  .breakdown-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.5rem;
    font-size: 0.8rem;
  }
  .breakdown-grid span {
    display: block;
    color: #6b7280;
  }

  .chart-wrapper {
    margin-top: 0.25rem;
  }
  .sq-chart {
    width: 100%;
    height: auto;
  }

  .session-cards .cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
    gap: 0.75rem;
    margin-top: 0.4rem;
  }
  .session-card {
    border-radius: 10px;
    border: 1px solid #e5e7eb;
    padding: 0.6rem 0.7rem;
    background: #f9fafb;
  }
  .header-row {
    display: flex;
    justify-content: space-between;
    gap: 0.75rem;
    align-items: flex-start;
    margin-bottom: 0.35rem;
  }
  .session-card .name {
    font-size: 0.95rem;
    font-weight: 600;
    color: #111827;
  }
  .score-pill {
    background: #2563eb;
    color: #ffffff;
    font-size: 0.9rem;
    font-weight: 600;
    padding: 0.2rem 0.5rem;
    border-radius: 999px;
    white-space: nowrap;
  }
  .components {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.2rem 0.5rem;
    font-size: 0.75rem;
    margin-bottom: 0.3rem;
  }
  .components span {
    color: #6b7280;
  }
  .components strong {
    margin-left: 0.25rem;
  }
  .small-meta {
    font-size: 0.75rem;
    color: #6b7280;
    display: flex;
    gap: 0.3rem;
    flex-wrap: wrap;
  }

  @media (max-width: 900px) {
    .layout {
      grid-template-columns: minmax(0, 1fr);
    }
    .summary-cards {
      grid-template-columns: minmax(0, 1fr);
    }
  }
</style>
