<script lang="ts">
  import type { ClimbInput } from '$lib/types';
  export let climb: ClimbInput;
  export let onRemove: () => void;
</script>

<div class="climb-row">
  <div class="grid">
    <label>
      <span>Climb Name</span>
      <input type="text" bind:value={climb.name} placeholder="e.g., Moonboard 6B+" required />
    </label>
    <label>
      <span>Grade</span>
      <input type="number" bind:value={climb.grade} min="0" step="1" required />
    </label>
    <label>
      <span>Attempts</span>
      <input type="number" bind:value={climb.attempts} min="0" step="1" />
    </label>
    <label class="flags">
      <input type="checkbox" bind:checked={climb.flagBoulder} />
      <span>Boulder</span>
    </label>
    <label class="flags">
      <input type="checkbox" bind:checked={climb.flagSport} />
      <span>Sport</span>
    </label>
  </div>
  <button type="button" class="remove" on:click={onRemove} aria-label="Remove climb">✕</button>
</div>

<style>
  .climb-row { position: relative; border: 1px solid #eee; padding: 12px; border-radius: 10px; margin: 10px 0; }
  .climb-row .grid { display: grid; grid-template-columns: 2fr 1fr 1fr auto auto; gap: 12px; align-items: end; }
  label { display: grid; gap: 6px; font-size: 0.9rem; }
  input[type="text"], input[type="number"] { padding: 10px; border: 1px solid #cfd7df; border-radius: 8px; }
  .flags { display: flex; align-items: center; gap: 6px; }
  .remove { position: absolute; top: 8px; right: 8px; border: none; background: #f3f4f6; border-radius: 8px; padding: 4px 8px; cursor: pointer; }
</style>
