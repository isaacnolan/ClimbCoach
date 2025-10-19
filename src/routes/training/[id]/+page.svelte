<script lang="ts">
  export let data: {
    session: {
      id: string;
      name: string;
      scheduledDate: string;
      description: string | null;
      workout: { id: string; name: string; description: string | null; exercises: any[] } | null;
      climbs: Array<{
        id: string;
        name: string;
        grade: number;
        attempts: number;
        flagBoulder: boolean;
        flagSport: boolean;
      }>;
    };
  };

  const s = data.session;
  const fmt = (iso: string) => new Date(iso).toLocaleString();
</script>

<div class="ts">
  <div class="ts__header">
    <button class="ts__back" on:click={() => history.back()} aria-label="Back">←</button>
    <h1 class="ts__title">{s.name}</h1>
  </div>

  <div class="ts__meta">
    <div class="ts__row"><div class="ts__label">Scheduled</div><div class="ts__value">{fmt(s.scheduledDate)}</div></div>
    {#if s.description}
      <div class="ts__row"><div class="ts__label">Description</div><div class="ts__value">{s.description}</div></div>
    {/if}
  </div>

  <div class="ts__card">
    <h2>Workout</h2>
    {#if s.workout}
      <div class="ts__workout-name">{s.workout.name}</div>
      {#if s.workout.description}<p class="ts__muted">{s.workout.description}</p>{/if}
      {#if s.workout.exercises.length}
        <div class="ts__ex-list">
          {#each s.workout.exercises as ex}
            <div class="ts__ex-item">
              <div class="ts__ex-name">{ex.name}</div>
              <div class="ts__ex-meta">
                {ex.sets} sets
                {#if ex.reps} · {ex.reps} reps{/if}
                {#if ex.duration} · {ex.duration}s{/if}
                {#if ex.rest} · rest {ex.rest}s{/if}
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <div class="ts__muted">No exercises.</div>
      {/if}
    {:else}
      <div class="ts__muted">No linked workout.</div>
    {/if}
  </div>

  <div class="ts__card">
    <h2>Climbs</h2>
    {#if s.climbs.length}
      <div class="ts__climb-list">
        {#each s.climbs as c}
          <div class="ts__climb">
            <div class="ts__climb-name">{c.name}</div>
            <div class="ts__climb-meta">
              Grade {c.grade} · Attempts {c.attempts}{#if c.flagBoulder} · Boulder{/if}{#if c.flagSport} · Sport{/if}
            </div>
          </div>
        {/each}
      </div>
    {:else}
      <div class="ts__muted">No climbs added.</div>
    {/if}
  </div>
</div>

<style>
  .ts { max-width: 880px; margin: 0 auto; padding: 24px; }
  .ts__header { display:flex; align-items:center; gap:12px; margin-bottom:8px; }
  .ts__back { border:none; background:#eef2ff; border-radius:8px; padding:.4rem .6rem; cursor:pointer; }
  .ts__title { font-size: 1.8rem; margin: 0; }

  .ts__meta { background:#fff; border-radius:14px; box-shadow:0 1px 4px rgba(0,0,0,.06); padding:14px 16px; margin: 10px 0 22px; }
  .ts__row { display:flex; gap:16px; padding:6px 0; }
  .ts__label { width:120px; color:#64748b; font-weight:600; }
  .ts__value { color:#0f172a; }

  .ts__card { background:#fff; border-radius:14px; box-shadow:0 1px 4px rgba(0,0,0,.06); padding:16px; margin-bottom:18px; }
  .ts__workout-name { font-weight:700; margin-bottom:6px; }
  .ts__ex-list { display:flex; flex-direction:column; gap:10px; margin-top:8px; }
  .ts__ex-item { display:flex; justify-content:space-between; border-bottom:1px solid #f1f5f9; padding-bottom:8px; }
  .ts__ex-item:last-child { border-bottom:none; }
  .ts__ex-name { font-weight:600; }
  .ts__ex-meta { color:#475569; font-size:.92rem; }

  .ts__climb-list { display:flex; flex-direction:column; gap:10px; }
  .ts__climb { display:flex; justify-content:space-between; border-bottom:1px solid #f1f5f9; padding-bottom:8px; }
  .ts__climb:last-child { border-bottom:none; }
  .ts__climb-name { font-weight:600; }
  .ts__climb-meta { color:#475569; font-size:.92rem; }

  .ts__muted { color:#64748b; }
</style>
