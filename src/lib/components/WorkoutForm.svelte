<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher<{ workoutCreated: { workout: any } }>();

  type ExerciseRow = {
    name: string;
    sets: number;
    reps?: number | null;
    duration?: number | null;
    rest?: number | null;
    orderIdx?: number | null;
  };

  let name = '';
  let description: string | null = '';
  let exercises: ExerciseRow[] = [
    { name: '', sets: 3, reps: 8, duration: null, rest: 60, orderIdx: 1 }
  ];

  function addExercise() {
    exercises = [
      ...exercises,
      { name: '', sets: 3, reps: 8, duration: null, rest: 60, orderIdx: (exercises.at(-1)?.orderIdx ?? 0) + 1 }
    ];
  }
  function removeExercise(i: number) { exercises = exercises.filter((_, idx) => idx !== i); }

  async function submit() {
    if (!name.trim()) return alert('Workout name required');

    const payload = {
      name,
      description: description || null,
      exercises: exercises.map((e, i) => ({
        name: e.name,
        sets: Number(e.sets || 0),
        reps: e.reps != null ? Number(e.reps) : null,
        duration: e.duration != null ? Number(e.duration) : null,
        rest: e.rest != null ? Number(e.rest) : null,
        orderIdx: e.orderIdx != null ? Number(e.orderIdx) : i + 1
      }))
    };

    const res = await fetch('/api/workouts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const e = await res.json().catch(() => ({}));
      alert(e?.error || 'Failed to create workout');
      return;
    }
    const created = await res.json();

    // 🔔 IMPORTANT: emit the created workout so others (TrainingSessionForm) can auto-select it
    dispatch('workoutCreated', { workout: created });

    // reset form (keeps same UX as before)
    name = '';
    description = '';
    exercises = [{ name: '', sets: 3, reps: 8, duration: null, rest: 60, orderIdx: 1 }];
  }
</script>

<div class="card">
  <label>
    <span>Workout Name</span>
    <input placeholder="e.g., Hangboard Repeaters" bind:value={name} />
  </label>

  <label>
    <span>Description</span>
      <textarea rows="3" placeholder="Optional description" bind:value={description}></textarea>
  </label>

  <h3>Exercises</h3>
  {#each exercises as ex, i}
    <div class="ex-row">
      <input placeholder="Exercise Name" bind:value={ex.name} />
      <input type="number" min="1" step="1" placeholder="Sets" bind:value={ex.sets} />
      <input type="number" min="0" step="1" placeholder="Reps" bind:value={ex.reps} />
      <input type="number" min="0" step="1" placeholder="Duration (sec)" bind:value={ex.duration} />
      <input type="number" min="0" step="1" placeholder="Rest (sec)" bind:value={ex.rest} />
      <button type="button" class="remove" on:click={() => removeExercise(i)}>✕</button>
    </div>
  {/each}
  <button type="button" class="ghost" on:click={addExercise}>+ Add Exercise</button>

  <div class="actions">
    <button on:click={submit}>Add Workout</button>
  </div>
</div>

<style>
  .card { background:white; padding:1.5rem; border-radius:12px; box-shadow:0 2px 4px rgba(0,0,0,.1); display:grid; gap:12px; }
  label { display:grid; gap:6px; }
  input, textarea { padding:.75rem; border:1px solid #cfd7df; border-radius:8px; }
  .ex-row { display:grid; grid-template-columns:2fr 1fr 1fr 1fr 1fr auto; gap:8px; align-items:center; }
  .ghost { background:transparent; border:1px dashed #cbd5e1; border-radius:10px; padding:8px 12px; }
  .actions { display:flex; justify-content:flex-end; }
  .actions button { background:#3498db; color:#fff; border:none; padding:.75rem 1.25rem; border-radius:8px; }
  .remove { border:none; background:#f3f4f6; border-radius:8px; padding:6px 10px; cursor:pointer; }
</style>
