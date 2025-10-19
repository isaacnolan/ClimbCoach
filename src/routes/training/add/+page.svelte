<script lang="ts">
  import { onMount } from 'svelte';
  type WorkoutLite = { id: string; name: string; description?: string | null };
  type ClimbInput = { name: string; grade: number; flagBoulder?: boolean; flagSport?: boolean; attempts?: number };

  let workouts: WorkoutLite[] = [];
  let loadingWorkouts = true;
  let creatingWorkout = false;

  let name = '';
  let description = '';
  let scheduledDate = new Date().toISOString().slice(0,16); // yyyy-mm-ddThh:mm
  let workoutId = '';

  let newWorkoutName = '';
  let newWorkoutDescription = '';

  let climbs: ClimbInput[] = [{ name: '', grade: 0, flagBoulder: true, flagSport: false, attempts: 0 }];

  onMount(async () => {
    const res = await fetch('/api/workouts?lite=1').catch(() => null);
    if (res?.ok) {
      workouts = await res.json();
      if (workouts.length) workoutId = workouts[0].id;
    }
    loadingWorkouts = false;
  });

  function addClimb() {
    climbs = [...climbs, { name: '', grade: 0, flagBoulder: true, flagSport: false, attempts: 0 }];
  }
  function removeClimb(i: number) { climbs = climbs.filter((_, idx) => idx !== i); }

  async function quickCreateWorkout() {
    if (!newWorkoutName.trim()) return;
    creatingWorkout = true;
    try {
      const res = await fetch('/api/workouts', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ name:newWorkoutName, description:newWorkoutDescription })
      });
      if (!res.ok) { alert('Failed to create workout'); return; }
      const w = await res.json();
      workouts = [w, ...workouts]; workoutId = w.id;
      newWorkoutName=''; newWorkoutDescription='';
    } finally { creatingWorkout = false; }
  }

  async function submitForm() {
    if (!workoutId) { alert('Choose or create a workout first.'); return; }
    const payload = {
      name, description,
      scheduledDate: new Date(scheduledDate).toISOString(),
      workoutId,
      climbs: climbs.map(c => ({
        name: c.name, grade: Number(c.grade||0),
        flagBoulder: !!c.flagBoulder, flagSport: !!c.flagSport,
        attempts: Number(c.attempts||0)
      }))
    };
    const res = await fetch('/api/training', {
      method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)
    });
    if (!res.ok) { alert('Failed to create session'); return; }
    // go back to list so user immediately sees it
    window.location.href = '/training';
  }
</script>

<div class="page">
  <div class="header">
    <h2>Add a Training Session</h2>
    <a class="ghost" href="/training">Back to list</a>
  </div>

  <div class="card">
    <label><span>Session Name</span>
      <input type="text" bind:value={name} placeholder="e.g., Board PE Session" required />
    </label>

    <label><span>Scheduled Date & Time</span>
      <input type="datetime-local" bind:value={scheduledDate} />
    </label>

    <label><span>Description</span>
      <textarea bind:value={description} placeholder="Optional description" rows="3"></textarea>
    </label>

    <div class="row">
      <div class="col">
        <label><span>Workout</span>
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

      <div class="col create">
        <span class="muted">Quick create workout</span>
        <div class="inline">
          <input type="text" bind:value={newWorkoutName} placeholder="New workout name" />
          <input type="text" bind:value={newWorkoutDescription} placeholder="Description (optional)" />
          <button type="button" on:click={quickCreateWorkout} disabled={creatingWorkout}>
            {creatingWorkout ? 'Creating…' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  </div>

  <h3>Climbs</h3>
  <div class="climbs">
    {#each climbs as c, i}
      <div class="climb">
        <input type="text" bind:value={c.name} placeholder="e.g., Moonboard 6B+" />
        <input type="number" bind:value={c.grade} min="0" step="1" />
        <input type="number" bind:value={c.attempts} min="0" step="1" />
        <label><input type="checkbox" bind:checked={c.flagBoulder} /> Boulder</label>
        <label><input type="checkbox" bind:checked={c.flagSport} /> Sport</label>
        <button type="button" on:click={() => removeClimb(i)}>✕</button>
      </div>
    {/each}
    <button type="button" class="ghost" on:click={addClimb}>+ Add another climb</button>
  </div>

  <div class="actions">
    <button class="primary" on:click={submitForm}>Add Training Session</button>
  </div>
</div>

<style>
  .page { max-width: 960px; margin: 0 auto; padding: 20px; }
  .header { display:flex; justify-content:space-between; align-items:center; margin-bottom: 10px; }
  .card { border:1px solid #e5e7eb; border-radius:12px; padding:16px; display:grid; gap:14px; }
  label { display:grid; gap:6px; }
  input[type="text"], input[type="datetime-local"], select, textarea { padding:10px; border:1px solid #cfd7df; border-radius:8px; }
  .row { display:grid; grid-template-columns:1fr 1fr; gap:16px; align-items:end; }
  .inline { display:grid; grid-template-columns:1.2fr 1.6fr auto; gap:8px; }
  .muted { color:#6b7280; font-size:.9rem; }
  .climbs { margin-top:10px; }
  .climb { display:grid; grid-template-columns:2fr 1fr 1fr auto auto auto; gap:8px; align-items:center; margin-bottom:8px; }
  .ghost { background:transparent; border:1px dashed #cbd5e1; border-radius:10px; padding:8px 12px; text-decoration:none; }
  .actions { margin-top:18px; }
  .primary { background:#1e90ff; color:#fff; border:none; padding:10px 16px; border-radius:10px; cursor:pointer; }
</style>
