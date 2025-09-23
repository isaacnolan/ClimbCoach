<script lang="ts">
import { onMount } from 'svelte';
import { getWorkouts } from '$lib/data/workouts';

type WorkoutEvent = {
  id: string;
  date: string;
  title: string;
  description: string;
};

let events: WorkoutEvent[] = [];
let year = 2025;
let month = 8; // September (0-indexed)
let daysInMonth = new Date(year, month + 1, 0).getDate();
let firstDay = new Date(year, month, 1).getDay();
let calendar: (number|null)[][] = [];

let selectedEvent: WorkoutEvent | null = null;
let showModal = false;
let isLoading = true;
let error: string | null = null;

onMount(async () => {
  calendar = [];
  let day = 1;
  for (let i = 0; i < 6; i++) {
    let week: (number|null)[] = [];
    for (let j = 0; j < 7; j++) {
      if ((i === 0 && j < firstDay) || day > daysInMonth) {
        week.push(null);
      } else {
        week.push(day);
        day++;
      }
    }
    calendar.push(week);
  }

  try {
    isLoading = true;
    error = null;
    const workouts = await getWorkouts();
    // Map workouts to calendar events (use scheduledDate if available, else createdAt)
    events = workouts
      .filter((w: any) => w.scheduledDate || w.createdAt)
      .map((w: any) => ({
        id: w.id,
        date: (w.scheduledDate ? w.scheduledDate : w.createdAt).slice(0, 10),
        title: w.name,
        description: w.description || '',
      }));
  } catch (err) {
    error = 'Failed to load workouts.';
  } finally {
    isLoading = false;
  }
});

function getEvent(day: number) {
  const date = `${year}-09-${String(day).padStart(2, '0')}`;
  return events.find(e => e.date.endsWith(date));
}

function handleEventClick(event) {
  selectedEvent = event;
  showModal = true;
}

function closeModal() {
  showModal = false;
  selectedEvent = null;
}
</script>

<style>
.calendar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  margin: 0 auto;
}
.calendar {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1rem;
  background: #f8fafc;
  border-radius: 1rem;
  padding: 2rem;
  width: 100%;
  max-width: 900px;
  box-sizing: border-box;
}
.day {
  background: #fff;
  border-radius: 0.75rem;
  min-height: 100px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-start;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  position: relative;
  padding: 0.75rem;
}
.day.event {
  background: #e3f0ff;
  border: 1px solid #3182ce;
}
.event-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #3182ce;
  position: absolute;
  top: 8px;
  right: 8px;
}
.event-title {
  color: #3182ce;
  font-weight: 500;
  margin-top: 0.5rem;
  font-size: 0.95rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
}
.header {
  text-align: center;
  font-size: 2rem;
  font-weight: bold;
  color: #3182ce;
  margin-bottom: 2rem;
}
.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  margin-bottom: 1rem;
  color: #94a3b8;
  font-weight: 500;
  font-size: 1.1rem;
  max-width: 900px;
  width: 100%;
  box-sizing: border-box;
}
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0,0,0,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal {
  background: #fff;
  padding: 2rem;
  border-radius: 1rem;
  box-shadow: 0 2px 16px rgba(0,0,0,0.15);
  min-width: 320px;
  max-width: 90vw;
}
</style>

<div class="calendar-container">
  <div class="header">September 2025</div>
  <div class="weekdays">
    <div>Sun</div>
    <div>Mon</div>
    <div>Tue</div>
    <div>Wed</div>
    <div>Thu</div>
    <div>Fri</div>
    <div>Sat</div>
  </div>
  {#if isLoading}
    <div class="loading">Loading workouts...</div>
  {:else if error}
    <div class="error-message">{error}</div>
  {:else}
    <div class="calendar">
      {#each calendar as week}
        {#each week as day}
          {#if day}
            <div class="day {getEvent(day) ? 'event' : ''}">
              {#if getEvent(day)}
                <div class="event-dot"></div>
                <div class="event-title" on:click={() => handleEventClick(getEvent(day))}>
                  {getEvent(day).title}
                </div>
              {/if}
            </div>
          {:else}
            <div class="day"></div>
          {/if}
        {/each}
      {/each}
    </div>
  {/if}

  {#if showModal && selectedEvent}
    <div class="modal-overlay" on:click={closeModal}>
      <div class="modal" on:click|stopPropagation>
        <h2>{selectedEvent.title}</h2>
        <p>{selectedEvent.description}</p>
        <p><strong>Date:</strong> {selectedEvent.date}</p>
        <button on:click={closeModal}>Close</button>
      </div>
    </div>
  {/if}
</div>
