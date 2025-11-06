<script lang="ts">
  export let sessionLoads: { scheduledDate: string; name: string; load: number }[] = [];
  export let acwrSeries: { ewma7Series?: number[]; ewma42Series?: number[] } | null = null;

  // Chart sizing
  const viewW = 600;
  const viewH = 180;
  const margin = { top: 12, right: 12, bottom: 36, left: 48 };
  const chartW = viewW - margin.left - margin.right;
  const chartH = viewH - margin.top - margin.bottom;

  // derived data
  $: loads = sessionLoads.map(s => s.load);
  $: maxLoad = Math.max(...loads, 1);
  $: n = Math.max(1, sessionLoads.length);

  // ticks for grid and y labels
  $: ticks = Array.from({ length: 5 }, (_, i) => {
    const t = i / 4;
    return { t, val: (1 - t) * maxLoad, y: margin.top + t * chartH };
  });

  function x(i: number) {
    return margin.left + (i / Math.max(1, n - 1)) * chartW;
  }

  function y(v: number) {
    // clamp
    const val = Number.isFinite(v) ? v : 0;
    return margin.top + (chartH - (val / maxLoad) * chartH);
  }

  $: points = sessionLoads.map((s, i) => ({ x: x(i), y: y(s.load), load: s.load, date: s.scheduledDate }));

  function pathFromPoints(pts: { x: number; y: number }[]) {
    if (!pts.length) return '';
    return pts.map((p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`)).join(' ');
  }

  $: loadPath = pathFromPoints(points.map(p => ({ x: p.x, y: p.y })));

  $: e7pts = (acwrSeries?.ewma7Series || []).map((v, i) => ({ x: x(i), y: y(v) }));
  $: e42pts = (acwrSeries?.ewma42Series || []).map((v, i) => ({ x: x(i), y: y(v) }));
  $: e7Path = pathFromPoints(e7pts);
  $: e42Path = pathFromPoints(e42pts);

  // tooltip
  let hoverIndex: number | null = null;
  let tooltipX = 0;
  let tooltipY = 0;

  function onMove(evt: MouseEvent) {
    const svg = (evt.currentTarget as SVGElement);
    const rect = svg.getBoundingClientRect();
    const mx = evt.clientX - rect.left;
    // find nearest index
    let nearest = 0;
    let best = Infinity;
    for (let i = 0; i < n; i++) {
      const dx = Math.abs(mx - x(i));
      if (dx < best) {
        best = dx;
        nearest = i;
      }
    }
    hoverIndex = nearest;
    tooltipX = x(nearest);
    tooltipY = y(points[nearest].load) - 8;
  }

  function onLeave() {
    hoverIndex = null;
  }
</script>

<!-- Legend rendered outside the SVG to avoid covering the plot -->
<div class="chart-legend">
  <div class="legend-item"><span class="swatch session"></span>Session load</div>
  <div class="legend-item"><span class="swatch fatigue"></span>Fatigue (7d)</div>
  <div class="legend-item"><span class="swatch fitness"></span>Fitness (42d)</div>
</div>

<svg viewBox={`0 0 ${viewW} ${viewH}`} width="100%" height="180" on:mousemove={onMove} on:mouseleave={onLeave} role="img" aria-label="Training load chart">
  <!-- background -->
  <rect x="0" y="0" width="100%" height="100%" fill="transparent" />

  <!-- grid lines & y labels -->
  {#each ticks as tick}
    <line x1={margin.left} x2={margin.left + chartW} y1={tick.y} y2={tick.y} stroke="#eee" />
    <text x={margin.left - 8} y={tick.y + 4} text-anchor="end" font-size="11" fill="#666">{tick.val.toFixed(1)}</text>
  {/each}

  <!-- x axis labels (sparse) -->
  {#each sessionLoads as s, i}
    {#if i === 0 || i === n - 1 || (n <= 12 ? i % Math.ceil(n / 8) === 0 : i % Math.ceil(n / 12) === 0)}
      <text x={x(i)} y={margin.top + chartH + 20} font-size="10" text-anchor="middle" fill="#666">{new Date(s.scheduledDate).toLocaleDateString()}</text>
    {/if}
  {/each}

  <!-- area baseline shadow of loads for clarity -->
  {#if points.length}
    <path d={loadPath} fill="none" stroke="#2b6cb0" stroke-width="2" />
  {/if}

  {#if e42Path}
    <path d={e42Path} fill="none" stroke="#718096" stroke-width="2" stroke-dasharray="6,4" />
  {/if}
  {#if e7Path}
    <path d={e7Path} fill="none" stroke="#f6ad55" stroke-width="2" />
  {/if}

  <!-- points -->
  {#each points as p, i}
    <circle cx={p.x} cy={p.y} r={hoverIndex === i ? 4 : 3} fill={hoverIndex === i ? '#0b69ff' : '#1f6feb'} />
  {/each}

  <!-- invisible overlay for pointer capture -->
  <rect x={margin.left} y={margin.top} width={chartW} height={chartH} fill="transparent" />

  <!-- tooltip -->
  {#if hoverIndex !== null}
    <g transform={`translate(${tooltipX+8}, ${tooltipY-16})`}>
      <rect x="0" y="0" rx="4" ry="4" width="160" height="48" fill="#fff" stroke="#ddd" />
      <text x="8" y="16" font-size="12" fill="#222">{new Date(points[hoverIndex].date).toLocaleDateString()}</text>
      <text x="8" y="34" font-size="12" fill="#222">Load: {points[hoverIndex].load.toFixed(2)}</text>
      {#if acwrSeries?.ewma7Series}
        <text x="84" y="16" font-size="12" fill="#f6ad55">Fatigue: {(acwrSeries.ewma7Series?.[hoverIndex] ?? NaN).toFixed(2)}</text>
      {/if}
      {#if acwrSeries?.ewma42Series}
        <text x="84" y="34" font-size="12" fill="#718096">Fitness: {(acwrSeries.ewma42Series?.[hoverIndex] ?? NaN).toFixed(2)}</text>
      {/if}
    </g>
  {/if}

  <!-- legend moved outside SVG -->
</svg>

<style>
  svg { background: #fff; border-radius: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.03); }
  .chart-legend {
    display:flex;
    gap:12px;
    align-items:center;
    margin-bottom:8px;
    padding:6px 8px;
    background: rgba(255,255,255,0.95);
    border-radius:8px;
    border:1px solid #eee;
    max-width:100%;
  }
  .chart-legend .legend-item { display:flex; align-items:center; gap:8px; font-size:13px; color:#333 }
  .chart-legend .swatch { width:14px; height:10px; border-radius:2px; display:inline-block }
  .chart-legend .swatch.session { background: #1f6feb }
  .chart-legend .swatch.fatigue { background: #f6ad55 }
  .chart-legend .swatch.fitness { background: #718096 }
</style>
