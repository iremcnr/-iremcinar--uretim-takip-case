import type { Layout } from 'plotly.js';

/** Temiz, okunabilir grafik teması — tek renk paleti */
export const dashLayout: Partial<Layout> = {
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: '#fafafa',
  font: { family: 'Inter, system-ui, sans-serif', color: '#475569', size: 13 },
  margin: { t: 24, r: 48, b: 64, l: 56 },
  hovermode: 'closest',
  showlegend: false,
  xaxis: {
    gridcolor: '#f1f5f9',
    linecolor: '#e2e8f0',
    tickfont: { size: 11, color: '#64748b' },
    automargin: true,
  },
  yaxis: {
    gridcolor: '#f1f5f9',
    linecolor: '#e2e8f0',
    tickfont: { size: 11, color: '#64748b' },
    automargin: true,
  },
};

export const dashConfig = {
  displayModeBar: false,
  responsive: true,
};

export const CHART_COLOR = '#4f46e5';
export const CHART_COLOR_LIGHT = '#818cf8';
export const CHART_TEXT = { size: 11, color: '#334155' };

export function formatPercent(value: number, digits = 1): string {
  return `${value.toFixed(digits)}%`;
}

/** Trend grafiğinde yalnızca min, max ve son günü etiketle — üst üste binmeyi önler */
export function buildTrendHighlightAnnotations(dates: string[], values: number[]) {
  if (values.length === 0) return [];

  const lastIdx = values.length - 1;
  let minIdx = 0;
  let maxIdx = 0;

  values.forEach((v, i) => {
    if (v < values[minIdx]) minIdx = i;
    if (v > values[maxIdx]) maxIdx = i;
  });

  const highlights = [
    { idx: minIdx, label: 'Min', ay: 32 },
    { idx: maxIdx, label: 'Max', ay: -32 },
    { idx: lastIdx, label: 'Son', ay: -32 },
  ];

  const seen = new Set<number>();
  return highlights
    .filter(({ idx }) => {
      if (seen.has(idx)) return false;
      seen.add(idx);
      return true;
    })
    .map(({ idx, label, ay }) => ({
      x: dates[idx],
      y: values[idx],
      text: `<b>${label}</b><br>${formatPercent(values[idx])}`,
      showarrow: true,
      arrowhead: 0,
      arrowwidth: 1,
      arrowcolor: '#cbd5e1',
      ax: 0,
      ay,
      bgcolor: 'rgba(255,255,255,0.95)',
      bordercolor: '#e2e8f0',
      borderwidth: 1,
      borderpad: 5,
      font: { size: 11, color: '#334155' },
    }));
}
