<script lang="ts">
  export let sessionLoads: { scheduledDate: string; name: string; load: number }[] = [];
  export let acwrSeries: { ewma7Series?: number[]; ewma42Series?: number[] } | null = null;

  const viewW = 600;
  const viewH = 140;
  const margin = { top: 12, right: 12, bottom: 36, left: 48 };
  const chartW = viewW - margin.left - margin.right;
  const chartH = viewH - margin.top - margin.bottom;

  $: n = Math.max(1, sessionLoads.length);

  // compute ACWR ratios
  $: ratios = (() => {
    const e7 = acwrSeries?.ewma7Series ?? [];
    const e42 = acwrSeries?.ewma42Series ?? [];
    const out: number[] = [];
    for (let i = 0; i < Math.max(e7.length, e42.length, n); i++) {
      const a = e7[i];
      const b = e42[i];
      if (typeof a === 'number' && typeof b === 'number' && Number.isFinite(a) && Number.isFinite(b) && b !== 0) {
        out.push(a / b);
      } else {
        out.push(NaN);
      }
    }
    return out;
  })();

  $: valid = ratios.filter(v => Number.isFinite(v));
  $: minR = valid.length ? Math.min(...valid) : 0.5;
  $: maxR = valid.length ? Math.max(...valid) : 1.5;
  // pad a bit
  $: yMin = Math.max(0, minR - 0.2);
  $: yMax = maxR + 0.2;

  function x(i: number) {
    return margin.left + (i / Math.max(1, n - 1)) * chartW;
  }

  function y(v: number) {
    const val = Number.isFinite(v) ? v : yMin;
    const t = (val - yMin) / Math.max(1e-6, yMax - yMin);
    return margin.top + (1 - t) * chartH;
  }

  function pathFrom(vals: number[]) {
    const pts = vals.map((v, i) => ({ x: x(i), y: y(v) }));
    return pts.map((p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`)).join(' ');
  }

  $: acwrPath = pathFrom(ratios.map(v => Number.isFinite(v) ? v : yMin));

  // thresholds for colored zones
  const low = 0.8;
  const high = 1.5;

  $: yLow = y(low);
  $: yHigh = y(high);

  let hoverIndex: number | null = null;
  let tooltipX = 0;
  let tooltipY = 0;

  function onMove(evt: MouseEvent) {
    const svg = evt.currentTarget as SVGElement;
    const rect = svg.getBoundingClientRect();
    const mx = evt.clientX - rect.left;
    let nearest = 0;
    let best = Infinity;
    for (let i = 0; i < n; i++) {
      const dx = Math.abs(mx - x(i));
      if (dx < best) { best = dx; nearest = i; }
    }
    hoverIndex = nearest;
    tooltipX = x(nearest);
    tooltipY = y(Number.isFinite(ratios[nearest]) ? ratios[nearest] : yMin) - 8;
  }
  function onLeave() { hoverIndex = null; }
</script>

<!-- Legend rendered outside the SVG so it never covers the plot -->
<div class="acwr-legend">
  <div class="legend-item"><span class="swatch under"></span>Undertraining (&lt; 0.8)</div>
  <div class="legend-item"><span class="swatch optimal"></span>Optimal (0.8–1.5)</div>
  <div class="legend-item"><span class="swatch over"></span>Overtraining (&gt; 1.5)</div>
</div>

<svg viewBox={`0 0 ${viewW} ${viewH}`} width="100%" height="140" on:mousemove={onMove} on:mouseleave={onLeave} role="img" aria-label="ACWR chart">
  <!-- background -->
  <rect x="0" y="0" width="100%" height="100%" fill="transparent" />

  <!-- colored zones: draw three stacked rects -->
  <!-- area above high -> red -->
  <rect x={margin.left} y={0} width={chartW} height={yHigh - margin.top} fill="#fed7d7" />
  <!-- green zone -->
  <rect x={margin.left} y={yHigh} width={chartW} height={yLow - yHigh} fill="#e6ffed" />
  <!-- below low -> red/pale -->
  <rect x={margin.left} y={yLow} width={chartW} height={margin.top + chartH - yLow} fill="#fff0f0" />

  <!-- grid lines and labels -->
  {#each [yMax, (yMax + yMin)/2, yMin] as lab, i}
    <line x1={margin.left} x2={margin.left + chartW} y1={y(lab)} y2={y(lab)} stroke="#eee" />
  {/each}

  <!-- threshold lines -->
  <line x1={margin.left} x2={margin.left + chartW} y1={yLow} y2={yLow} stroke="#c53030" stroke-dasharray="4,3" />
  <line x1={margin.left} x2={margin.left + chartW} y1={yHigh} y2={yHigh} stroke="#c53030" stroke-dasharray="4,3" />

  <!-- x labels -->
  {#each sessionLoads as s, i}
    {#if i === 0 || i === n - 1 || (n <= 12 ? i % Math.ceil(n / 8) === 0 : i % Math.ceil(n / 12) === 0)}
      <text x={x(i)} y={margin.top + chartH + 20} font-size="10" text-anchor="middle" fill="#666">{new Date(s.scheduledDate).toLocaleDateString()}</text>
    {/if}
  {/each}

  <!-- ACWR line -->
  <path d={acwrPath} fill="none" stroke="#2b6cb0" stroke-width="2" />

  <!-- points -->
  {#each ratios as r, i}
    {#if Number.isFinite(r)}
      <circle cx={x(i)} cy={y(r)} r={hoverIndex === i ? 4 : 3} fill={hoverIndex === i ? '#0b69ff' : '#1f6feb'} />
    {/if}
  {/each}

  <!-- tooltip -->
  {#if hoverIndex !== null}
    {#if Number.isFinite(ratios[hoverIndex])}
      <g transform={`translate(${tooltipX+8}, ${tooltipY-16})`}>
        <rect x="0" y="0" rx="4" ry="4" width="140" height="44" fill="#fff" stroke="#ddd" />
        <text x="8" y="16" font-size="12" fill="#222">{new Date(sessionLoads[hoverIndex].scheduledDate).toLocaleDateString()}</text>
        <text x="8" y="34" font-size="12" fill="#222">ACWR: {ratios[hoverIndex].toFixed(2)}</text>
      </g>
    {/if}
  {/if}

  <!-- legend moved out of SVG -->
</svg>

<style>
  svg { background: #fff; border-radius: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.03); }
  .acwr-legend {
    display: flex;
    gap: 12px;
    align-items: center;
    margin-bottom: 8px;
    padding: 6px 8px;
    background: rgba(255,255,255,0.95);
    border-radius: 8px;
    border: 1px solid #eee;
    max-width: 100%;
  }
  .acwr-legend .legend-item { display:flex; align-items:center; gap:8px; font-size:13px; color:#333 }
  .acwr-legend .swatch { width:14px; height:10px; border-radius:2px; display:inline-block; }
  .acwr-legend .swatch.under { background:#fff0f0; }
  .acwr-legend .swatch.optimal { background:#e6ffed; }
  .acwr-legend .swatch.over { background:#fed7d7; }
</style>
