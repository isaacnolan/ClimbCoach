<script lang="ts">
  import { createWorkout } from '$lib/data/workouts';
  import { createEventDispatcher } from 'svelte';

  export let userId: string | undefined;

  const dispatch = createEventDispatcher();

  let workoutName = '';
  let workoutDescription = '';
  let exercises = [{ name: '', sets: 3, reps: 8, duration: null, rest: 60 }];

  let isSubmitting = false;
  let formError = '';

  function addExercise() {
    exercises = [...exercises, { name: '', sets: 3, reps: 8, duration: null, rest: 60 }];
  }

  function removeExercise(index: number) {
    exercises = exercises.filter((_, i) => i !== index);
  }

  async function handleSubmit() {
    try {
      isSubmitting = true;
      formError = '';
      await createWorkout({
        userId,
        name: workoutName,
        description: workoutDescription,
        exercises: exercises.map((ex) => ({
          name: ex.name,
          sets: ex.sets,
          reps: ex.reps ?? undefined,
          duration: ex.duration ?? undefined,
          rest: ex.rest ?? undefined
        })),
      });
      workoutName = '';
      workoutDescription = '';
      exercises = [{ name: '', sets: 3, reps: 8, duration: null, rest: 60 }];
      dispatch('workoutCreated');
    } catch (error) {
      console.error('Error creating workout:', error);
      formError = 'Failed to create workout. Please try again later.';
    } finally {
      isSubmitting = false;
    }
  }
</script>

<form on:submit|preventDefault={handleSubmit} class="workout-form">
  {#if formError}
    <div class="error-message"><p>{formError}</p></div>
  {/if}

  <div class="form-group">
    <label for="workoutName">Workout Name</label>
    <input id="workoutName" bind:value={workoutName} required placeholder="e.g., Hangboard Repeaters" />
  </div>

  <div class="form-group">
    <label for="workoutDescription">Description</label>
    <textarea id="workoutDescription" bind:value={workoutDescription} placeholder="Optional description"></textarea>
  </div>

  <div class="exercises">
    <h3>Exercises</h3>
    {#each exercises as exercise, index}
      <div class="exercise-card">
        <button type="button" class="remove-btn" on:click={() => removeExercise(index)}>×</button>
        <div class="form-group">
          <label for={"exerciseName-" + index}>Exercise Name</label>
          <input id={"exerciseName-" + index} bind:value={exercise.name} required />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label for={"sets-" + index}>Sets</label>
            <input id={"sets-" + index} type="number" bind:value={exercise.sets} min="1" required />
          </div>
          <div class="form-group">
            <label for={"reps-" + index}>Reps</label>
            <input id={"reps-" + index} type="number" bind:value={exercise.reps} min="1" />
          </div>
          <div class="form-group">
            <label for={"duration-" + index}>Duration (sec)</label>
            <input id={"duration-" + index} type="number" bind:value={exercise.duration} min="1" />
          </div>
          <div class="form-group">
            <label for={"rest-" + index}>Rest (sec)</label>
            <input id={"rest-" + index} type="number" bind:value={exercise.rest} min="0" />
          </div>
        </div>
      </div>
    {/each}

    <button type="button" class="add-exercise-btn" on:click={addExercise}>Add Exercise</button>
  </div>

  <button type="submit" class="submit-btn" disabled={isSubmitting}>
    {isSubmitting ? 'Creating…' : 'Create Workout'}
  </button>
</form>

<style>
  .workout-form { max-width: 800px; margin: 0 auto; padding: 2rem; }
  .form-group { margin-bottom: 1rem; }
  label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
  input, textarea { width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem; }
  textarea { min-height: 100px; resize: vertical; }
  .exercises { margin: 2rem 0; }
  .exercise-card { position: relative; background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 1rem; }
  .remove-btn { position: absolute; top: 0.5rem; right: 0.5rem; background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #666; }
  .form-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-top: 1rem; }
  .add-exercise-btn { background: #f5f5f5; border: none; padding: 0.8rem 1.5rem; border-radius: 4px; cursor: pointer; margin: 1rem 0; width: 100%; }
  .submit-btn { background: #3498db; color: white; border: none; padding: 1rem 2rem; border-radius: 4px; cursor: pointer; font-size: 1.1rem; width: 100%; }
  .submit-btn:hover { background: #2980b9; }
</style>
