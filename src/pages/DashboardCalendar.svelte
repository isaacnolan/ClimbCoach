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

const monthNames = [
  'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'
];

function updateCalendar() {
  daysInMonth = new Date(year, month + 1, 0).getDate();
  firstDay = new Date(year, month, 1).getDay();
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
}

function prevMonth() {
  if (month === 0) {
    month = 11;
    year--;
  } else {
    month--;
  }
  updateCalendar();
}

function nextMonth() {
  if (month === 11) {
    month = 0;
    year++;
  } else {
    month++;
  }
  updateCalendar();
}

let selectedEvent: WorkoutEvent | null = null;
let showModal = false;
let isLoading = true;
let error: string | null = null;

onMount(async () => {
  updateCalendar();
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
        exercises: w.exercises || [],
      }));
  } catch (err) {
    error = 'Failed to load workouts.';
  } finally {
    isLoading = false;
  }
});

function getEvent(day: number) {
  const date = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
  return events.find(e => e.date === date);
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
/* Modal styles improved */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(44,62,80,0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal {
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 320px;
  max-width: 90vw;
}
.modal-content {
  background: #fff;
  border-radius: 1.25rem;
  box-shadow: 0 8px 32px rgba(44,62,80,0.18);
  padding: 2.5rem 2rem 2rem 2rem;
  min-width: 320px;
  max-width: 400px;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}
.modal-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}
.modal-desc {
  color: #444;
  font-size: 1.05rem;
  margin-bottom: 0.5rem;
}
.modal-date-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  font-size: 1rem;
}
.modal-date-label {
  font-weight: 500;
  color: #3182ce;
}
.modal-date-value {
  color: #2c3e50;
}
.modal-close {
  align-self: flex-end;
  background: #3498db;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0.6rem 1.2rem;
  font-size: 1rem;
  cursor: pointer;
  margin-top: 0.5rem;
  transition: background 0.2s;
}
.modal-close:hover {
  background: #2980b9;
}
</style>

<div class="calendar-container">
  <div class="header" style="display: flex; align-items: center; justify-content: center; gap: 1.5rem;">
    <button style="background: #e3f0ff; color: #3182ce; border: none; border-radius: 8px; padding: 0.4rem 1rem; font-size: 1.1rem; cursor: pointer; font-weight: 500;" on:click={prevMonth}>&lt;</button>
    <span>{monthNames[month]} {year}</span>
    <button style="background: #e3f0ff; color: #3182ce; border: none; border-radius: 8px; padding: 0.4rem 1rem; font-size: 1.1rem; cursor: pointer; font-weight: 500;" on:click={nextMonth}>&gt;</button>
  </div>
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
              <span style="position: absolute; top: 8px; left: 10px; font-size: 0.95rem; color: #94a3b8; font-weight: 500;">{day}</span>
              {#if getEvent(day)}
                <div class="event-dot"></div>
                <div style="margin-top: 1.7rem;"></div> <!-- Spacer between number and title -->
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
        <div class="modal-content">
          <h2 class="modal-title">{selectedEvent.title}</h2>
          {#if selectedEvent.description}
            <p class="modal-desc">{selectedEvent.description}</p>
          {/if}
          {#if selectedEvent.exercises && selectedEvent.exercises.length > 0}
            <div>
              <h3 style="margin: 0.5rem 0 0.2rem 0; font-size: 1.1rem; color: #3182ce;">Exercises</h3>
              <ul style="padding-left: 1.2rem;">
                {#each selectedEvent.exercises as ex}
                  <li style="margin-bottom: 0.5rem;">
                    <strong>{ex.name}</strong>
                    {#if ex.sets}
                      <span> — {ex.sets} sets</span>
                    {/if}
                    {#if ex.reps}
                      <span>, {ex.reps} reps</span>
                    {/if}
                    {#if ex.duration}
                      <span>, {ex.duration}s</span>
                    {/if}
                    {#if ex.rest}
                      <span>, rest: {ex.rest}s</span>
                    {/if}
                  </li>
                {/each}
              </ul>
            </div>
          {/if}
          <div class="modal-date-row" style="margin-top: 1.2rem; justify-content: left; align-self: center; width: 100%;">
            <span class="modal-date-label">Date:</span>
            <span class="modal-date-value">{selectedEvent.date}</span>
          </div>
          <button class="modal-close" on:click={closeModal}>Close</button>
        </div>
      </div>
    </div>
  {/if}
</div>
