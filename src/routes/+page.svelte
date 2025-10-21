<script lang="ts">
  import { onMount } from 'svelte';
  import { getWorkouts } from '$lib/data/workouts';
  import WorkoutForm from '$lib/components/WorkoutForm.svelte';
  import PerformanceAnalyzer from '$lib/components/PerformanceAnalyzer.svelte';
  import DashboardCalendar from '../pages/DashboardCalendar.svelte';
  import ProgressChart from '../pages/ProgressChart.svelte';
  import ChatBot from '$lib/components/ChatBot.svelte';

  // No filtering so everything shows
  const USER_ID: string | undefined = undefined;

  type Exercise = {
    id: string;
    name: string;
    description: string | null;
    sets: number;
    reps: number | null;
    duration: number | null;
    rest: number | null;
    workoutId: string;
  };

  type Workout = {
    id?: string;
    userId?: string | null;
    name: string;
    description: string | null;
    exercises: Exercise[];
  };

  let currentTab: 'dashboard' | 'workouts' | 'progress' | 'analyzer' = 'dashboard';
  let workouts: Workout[] = [];
  let showWorkoutForm = false;
  let isLoading = true;
  let error: string | null = null;

  async function loadWorkouts() {
    try {
      isLoading = true;
      error = null;
      workouts = await getWorkouts(); // no filter
    } catch (err) {
      console.error('Error loading workouts:', err);
      error = 'Failed to load workouts. Please try again later.';
    } finally {
      isLoading = false;
    }
  }

  function handleWorkoutCreated() {
    showWorkoutForm = false;
    loadWorkouts();
  }

  function handleTabClick(tab: typeof currentTab, event: MouseEvent) {
    event.preventDefault();
    currentTab = tab;
  }

  onMount(loadWorkouts);
</script>

<div class="container">
  <header class="header">
    <div class="header-left">
      <h1>ClimbBot</h1>
      <p class="subtitle">Your Personal Climbing Training Assistant</p>
    </div>
  </header>

  <nav class="tabs">
    <button class:active={currentTab === 'dashboard'} on:click={(e) => handleTabClick('dashboard', e)}>Dashboard</button>
    <button class:active={currentTab === 'workouts'} on:click={(e) => handleTabClick('workouts', e)}>Workouts</button>
    <button class:active={currentTab === 'progress'} on:click={(e) => handleTabClick('progress', e)}>Progress</button>
    <button class:active={currentTab === 'analyzer'} on:click={(e) => handleTabClick('analyzer', e)}>Performance Analyzer</button>
  </nav>

  <main>
    {#if error}
      <div class="error-message">
        <p>{error}</p>
        <button on:click={loadWorkouts}>Retry</button>
      </div>

    {:else if isLoading}
      <div class="loading">Loading...</div>

    {:else if currentTab === 'dashboard'}
      <section class="dashboard">
        <DashboardCalendar />
      </section>

    {:else if currentTab === 'workouts'}
      <section class="workouts">
        <div class="workouts-header">
          <h2>Your Workouts</h2>
          <button on:click={() => (showWorkoutForm = true)}>Add Workout</button>
        </div>

        {#if showWorkoutForm}
          <WorkoutForm on:workoutCreated={handleWorkoutCreated} />
        {:else if workouts.length === 0}
          <div class="empty-state">
            <p>You haven't created any workouts yet</p>
            <p class="empty-action">Click the "Add Workout" button to create your first workout</p>
          </div>
        {:else}
          <div class="workout-grid">
            {#each workouts as workout}
              <div class="workout-card">
                <h3>{workout.name}</h3>
                <p>{workout.description || 'No description'}</p>
                <div class="exercise-list">
                  {#each workout.exercises as exercise}
                    <div class="exercise-item">
                      <span class="exercise-name">{exercise.name}</span>
                      <span class="exercise-details">
                        {exercise.sets} sets
                        {#if exercise.reps}× {exercise.reps} reps{/if}
                        {#if exercise.duration} ({exercise.duration}s){/if}
                      </span>
                    </div>
                  {/each}
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </section>

    {:else if currentTab === 'analyzer'}
      <section class="analyzer-section">
        <PerformanceAnalyzer />
        <ChatBot />
      </section>

    {:else}
      <section class="progress">
        <h2>Your Progress</h2>
        <ProgressChart />
        <div class="progress-stats">
          <div class="stat"><h3>Max Grade</h3><p>V5</p></div>
          <div class="stat"><h3>Training Days</h3><p>12/30</p></div>
          <div class="stat"><h3>Workouts</h3><p>{workouts.length}</p></div>
        </div>
      </section>
    {/if}
  </main>
</div>

<style>
  .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
  .header { display: flex; align-items: flex-end; justify-content: space-between; gap: 1rem; margin-bottom: 1.5rem; }
  .header-left h1 { font-size: 3rem; color: #2c3e50; margin-bottom: 0.5rem; }
  .subtitle { color: #7f8c8d; font-size: 1.1rem; }
  .tabs { display: flex; gap: 1rem; margin-bottom: 2rem; justify-content: center; }
  .tabs button { padding: 0.8rem 1.5rem; border: none; background: #f5f5f5; border-radius: 8px; cursor: pointer; transition: all 0.2s ease; }
  .tabs button.active { background: #3498db; color: white; }
  .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; }
  .card { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
  .workouts-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
  .workout-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; }
  .workout-card { background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
  .exercise-list { margin-top: 1rem; }
  .exercise-item { display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #eee; }
  .exercise-item:last-child { border-bottom: none; }
  .exercise-name { font-weight: 500; }
  .exercise-details { color: #666; }
  .progress-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 2rem; }
  .stat { text-align: center; padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
  button { background: #3498db; color: white; border: none; padding: 0.8rem 1.5rem; border-radius: 8px; cursor: pointer; transition: background 0.2s ease; }
  button:hover { background: #2980b9; }
  .error-message { text-align: center; padding: 2rem; background: #fee; border-radius: 8px; margin: 2rem 0; }
  .loading { text-align: center; padding: 2rem; font-size: 1.2rem; color: #666; }
  .empty-state { text-align: center; padding: 2rem; background: #f8f9fa; border-radius: 8px; margin: 2rem 0; border: 1px dashed #ddd; }
  .empty-action { margin-top: 0.5rem; color: #666; font-size: 0.9rem; }
  .analyzer-section { max-width: 1200px; margin: 0 auto; padding: 2rem; }
</style>
