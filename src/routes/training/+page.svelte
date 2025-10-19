<script lang="ts">
  export let data: {
    sessions: Array<{
      id: string;
      name: string;
      scheduledDate: string;
      description: string | null;
      workout: { id: string; name: string | null } | null;
      climbs: Array<{ id: string }>;
    }>;
  };
  const fmt = (dt: string) => new Date(dt).toLocaleString();
</script>

<div class="page">
  <div class="header">
    <h2>Your Training Sessions</h2>
    <a href="/training/add" class="add">Add Training Session</a>
  </div>

  {#if data.sessions.length === 0}
    <div class="empty">No training sessions yet
      <div class="muted">Click “Add Training Session” to create your first one</div>
    </div>
  {:else}
    <div class="list">
      {#each data.sessions as s}
        <a class="item" href={`/training/${s.id}`}>
          <div class="title">{s.name}</div>
          <div class="meta">
            <span>{fmt(s.scheduledDate)}</span><span>•</span>
            <span>Workout: {s.workout?.name ?? '—'}</span><span>•</span>
            <span>{s.climbs.length} {s.climbs.length === 1 ? 'climb' : 'climbs'}</span>
          </div>
        </a>
      {/each}
    </div>
  {/if}
</div>

<style>
  .page { max-width: 980px; margin: 0 auto; padding: 20px; }
  .header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
  .add { background:#1e90ff; color:#fff; padding:8px 12px; border-radius:8px; text-decoration:none; }
  .empty { border:1px dashed #e5e7eb; background:#f8fafc; border-radius:12px; padding:28px; text-align:center; color:#111827; }
  .muted { color:#6b7280; margin-top:6px; }
  .list { display:grid; gap:12px; }
  .item { text-decoration:none; color:inherit; border:1px solid #e5e7eb; border-radius:12px; padding:12px; }
  .title { font-weight:600; }
  .meta { margin-top:6px; color:#6b7280; display:flex; gap:8px; font-size:.9rem; }
</style>
