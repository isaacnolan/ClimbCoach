<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import { createTrainingSession, type ClimbInput, type TrainingSessionInput } from '$lib/data/trainingSessions';
  import WorkoutForm from '$lib/components/WorkoutForm.svelte';

  const dispatch = createEventDispatcher<{ sessionCreated: void }>();

  type WorkoutLite = { id: string; name: string; description?: string | null };

  // form fields
  let name = '';
  let description = '';
  let scheduledDate = new Date().toISOString().slice(0, 16); // for datetime-local
  let workoutId = '';

  // workouts select
  let workouts: WorkoutLite[] = [];
  let loadingWorkouts = true;

  // show/hide inline workout creator
  let showInlineWorkout = false;

  // climbs
  let climbs: ClimbInput[] = [
    { name: '', grade: 0, attempts: 0, flagBoulder: true, flagSport: false }
  ];

  onMount(async () => {
    const res = await fetch('/api/workouts?lite=1').catch(() => null);
    if (res?.ok) {
      workouts = await res.json();
      if (workouts.length) workoutId = workouts[0].id;
    }
    loadingWorkouts = false;
  });

  function addClimb() {
    climbs = [...climbs, { name: '', grade: 0, attempts: 0, flagBoulder: true, flagSport: false }];
  }
  function removeClimb(i: number) { climbs = climbs.filter((_, idx) => idx !== i); }

  // When inline WorkoutForm creates a workout, it now emits { workout } (see next section)
  async function handleInlineWorkoutCreated(ev: CustomEvent<{ workout: WorkoutLite }>) {
    const created = ev.detail.workout;
    // prepend to list and select it
    workouts = [created, ...workouts];
    workoutId = created.id;
    showInlineWorkout = false;
  }

  async function submit() {
    if (!name.trim()) return alert('Session name required');
    if (!workoutId)    return alert('Pick or create a workout');

    const payload: TrainingSessionInput = {
      name,
      description,
      scheduledDate: new Date(scheduledDate).toISOString(),
      workoutId,
      climbs: climbs.map(c => ({
        name: c.name,
        grade: Number(c.grade || 0),
        attempts: Number(c.attempts || 0),
        flagBoulder: !!c.flagBoulder,
        flagSport: !!c.flagSport
      }))
    };

    await createTrainingSession(payload);
    dispatch('sessionCreated');
  }
</script>

<div class="card">
  <label>
    <span>Session Name</span>
    <input placeholder="e.g., Board PE Session" bind:value={name} />
  </label>

  <label>
    <span>Scheduled Date & Time</span>
    <input type="datetime-local" bind:value={scheduledDate} />
  </label>

  <label>
    <span>Description</span>
    <textarea rows="3" placeholder="Optional description" bind:value={description} />
  </label>

  <div class="row">
    <div class="col">
      <label>
        <span>Attach Workout</span>
        {#if loadingWorkouts}
          <div class="muted">Loading workouts…</div>
        {:else}
          <select bind:value={workoutId}>
            <option value="" disabled>Select workout</option>
            {#each workouts as w}<option value={w.id}>{w.name}</option>{/each}
          </select>
        {/if}
      </label>
    </div>

    <div class="col align-end">
      <button type="button" class="ghost" on:click={() => (showInlineWorkout = !showInlineWorkout)}>
        {showInlineWorkout ? 'Hide' : 'Create a workout (with exercises)'}
      </button>
    </div>
  </div>

  {#if showInlineWorkout}
    <div class="inline-workout">
      <h3>Create Workout</h3>
      <!-- We re-use your WorkoutForm. It now emits { workout } on 'workoutCreated'. -->
      <WorkoutForm on:workoutCreated={handleInlineWorkoutCreated} />
    </div>
  {/if}

  <h3>Climbs</h3>
  {#each climbs as c, i}
    <div class="climb-row">
      <input placeholder="e.g., Moonboard 6B+" bind:value={c.name} />
      <input type="number" min="0" step="1" placeholder="Grade" bind:value={c.grade} />
      <input type="number" min="0" step="1" placeholder="Attempts" bind:value={c.attempts} />
      <label class="flag"><input type="checkbox" bind:checked={c.flagBoulder} /> Boulder</label>
      <label class="flag"><input type="checkbox" bind:checked={c.flagSport} /> Sport</label>
      <button type="button" class="remove" on:click={() => removeClimb(i)}>✕</button>
    </div>
  {/each}
  <button type="button" class="ghost" on:click={addClimb}>+ Add another climb</button>

  <div class="actions">
    <button on:click={submit}>Add Training Session</button>
  </div>
</div>

<style>
  .card { background:white; padding:1.5rem; border-radius:12px; box-shadow:0 2px 4px rgba(0,0,0,.1); display:grid; gap:12px; }
  label { display:grid; gap:6px; }
  input, textarea, select { padding:.75rem; border:1px solid #cfd7df; border-radius:8px; }
  .muted { color:#6b7280; }
  .row { display:grid; grid-template-columns: 1fr auto; gap:16px; align-items:end; }
  .col.align-end { display:flex; justify-content:flex-end; }
  .ghost { background:transparent; border:1px dashed #cbd5e1; border-radius:10px; padding:8px 12px; }
  .inline-workout { border:1px solid #e5e7eb; border-radius:12px; padding:12px; }
  .climb-row { display:grid; grid-template-columns:2fr 1fr 1fr auto auto auto; gap:8px; align-items:center; }
  .flag { display:flex; align-items:center; gap:6px; }
  .actions { display:flex; justify-content:flex-end; }
  .actions button { background:#3498db; color:#fff; border:none; padding:.75rem 1.25rem; border-radius:8px; }
  .remove { border:none; background:#f3f4f6; border-radius:8px; padding:6px 10px; cursor:pointer; }
</style>
