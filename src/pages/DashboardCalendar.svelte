<script lang="ts">
  import { onMount } from 'svelte';

  const today = new Date();
  let year = today.getFullYear();
  let month = today.getMonth(); // 0-based
  let days: Date[] = [];

  type LiteSession = { id: string; name: string; scheduledDate: string };
  let sessionsByDay: Record<string, LiteSession[]> = {};

  const ymd = (d: Date) => d.toISOString().slice(0, 10);
  const monthStart = (y: number, m: number) => new Date(y, m, 1, 0, 0, 0);
  const monthEnd = (y: number, m: number) => new Date(y, m + 1, 0, 23, 59, 59);

  function buildGrid() {
    const start = monthStart(year, month);
    const end = monthEnd(year, month);

    const firstGridDay = new Date(start);
    firstGridDay.setDate(firstGridDay.getDate() - firstGridDay.getDay());

    const lastGridDay = new Date(end);
    lastGridDay.setDate(lastGridDay.getDate() + (6 - lastGridDay.getDay()));

    const grid: Date[] = [];
    const cur = new Date(firstGridDay);
    while (cur <= lastGridDay) {
      grid.push(new Date(cur));
      cur.setDate(cur.getDate() + 1);
    }
    days = grid;
  }

  async function loadSessions() {
    const from = monthStart(year, month);
    const to = monthEnd(year, month);

    const url = new URL('/api/training', window.location.origin);
    url.searchParams.set('lite', '1');
    url.searchParams.set('from', from.toISOString());
    url.searchParams.set('to', to.toISOString());

    try {
      const res = await fetch(url.toString());
      if (!res.ok) {
        const fb = await fetch(
          `/api/training?from=${encodeURIComponent(from.toISOString())}&to=${encodeURIComponent(
            to.toISOString()
          )}`
        );
        if (!fb.ok) throw new Error('Failed to load training sessions');
        const full = await fb.json();
        indexSessions(full.map((s: any) => ({ id: s.id, name: s.name, scheduledDate: s.scheduledDate })));
        return;
      }
      const lite: LiteSession[] = await res.json();
      indexSessions(lite);
    } catch (e) {
      console.error('Calendar load error:', e);
      sessionsByDay = {};
    }
  }

  function indexSessions(items: LiteSession[]) {
    const map: Record<string, LiteSession[]> = {};
    for (const s of items) {
      const key = ymd(new Date(s.scheduledDate));
      (map[key] ||= []).push(s);
    }
    for (const k of Object.keys(map)) {
      map[k].sort((a, b) => +new Date(a.scheduledDate) - +new Date(b.scheduledDate));
    }
    sessionsByDay = map;
  }

  function prevMonth() {
    month === 0 ? (month = 11, year -= 1) : (month -= 1);
    buildGrid(); loadSessions();
  }
  function nextMonth() {
    month === 11 ? (month = 0, year += 1) : (month += 1);
    buildGrid(); loadSessions();
  }

  onMount(() => { buildGrid(); loadSessions(); });

  $: (year, month, buildGrid); // keep grid when the month/year changes
</script>

<div class="cc-cal">
  <div class="cc-cal__header">
    <button class="cc-cal__nav" on:click={prevMonth} aria-label="Previous month">‹</button>
    <h2 class="cc-cal__title">
      {new Date(year, month).toLocaleString(undefined, { month: 'long', year: 'numeric' })}
    </h2>
    <button class="cc-cal__nav" on:click={nextMonth} aria-label="Next month">›</button>
  </div>

  <div class="cc-cal__dow">
    <div>Sun</div><div>Mon</div><div>Tue</div><div>Wed</div><div>Thu</div><div>Fri</div><div>Sat</div>
  </div>

  <div class="cc-cal__grid">
    {#each days as d}
      {@const key = ymd(d)}
      <div class="cc-cal__cell {d.getMonth() !== month ? 'is-muted' : ''} {key === ymd(today) ? 'is-today' : ''}">
        <div class="cc-cal__date">{d.getDate()}</div>

        {#if sessionsByDay[key]}
          <div class="cc-cal__events">
            {#each sessionsByDay[key].slice(0, 2) as ev}
              <a class="cc-cal__event" href={`/training/${ev.id}`} title={ev.name}>
                <span class="cc-cal__dot" aria-hidden="true"></span>
                <span class="cc-cal__name">{ev.name}</span>
              </a>
            {/each}
            {#if sessionsByDay[key].length > 2}
              <div class="cc-cal__more">+{sessionsByDay[key].length - 2} more</div>
            {/if}
          </div>
        {/if}
      </div>
    {/each}
  </div>
</div>

<style>
  /* Namespaced everything with cc-cal__* so nothing global can collide */

  .cc-cal { margin: 0 auto; max-width: 980px; }

  .cc-cal__header {
    display:flex; align-items:center; justify-content:center; gap:16px; margin-bottom:14px;
  }
  .cc-cal__title { font-size: 2.25rem; color:#2563eb; font-weight:800; margin:0; }
  .cc-cal__nav { background:#eef2ff; border:none; border-radius:10px; padding:.4rem .7rem; cursor:pointer; }

  .cc-cal__dow {
    display:grid; grid-template-columns: repeat(7, 1fr);
    color:#94a3b8; font-weight:600; margin-bottom:8px;
  }

  .cc-cal__grid {
    display:grid; grid-template-columns: repeat(7, 1fr);
    gap:14px;
  }

  .cc-cal__cell {
    position:relative;
    padding:10px;
    aspect-ratio: 1 / 1;        /* ← keeps perfect squares */
    background:#f8fafc;
    border-radius:14px;
    box-shadow: inset 0 0 0 1px #eef2f7;
    overflow: hidden;
  }
  .cc-cal__cell.is-today { box-shadow: inset 0 0 0 2px #60a5fa; }
  .cc-cal__cell.is-muted { opacity:.55; }

  .cc-cal__date { color:#64748b; font-weight:700; }

  .cc-cal__events { margin-top:6px; display:flex; flex-direction:column; gap:4px; }
  .cc-cal__event {
    display:flex; align-items:center; gap:6px; text-decoration:none;
    font-size:.85rem; color:#1e3a8a; overflow:hidden;
  }
  .cc-cal__name { white-space:nowrap; text-overflow:ellipsis; overflow:hidden; }
  .cc-cal__dot { width:7px; height:7px; border-radius:50%; background:#1e90ff; display:inline-block; }
  .cc-cal__more { margin-top:2px; font-size:.8rem; color:#475569; }
</style>
