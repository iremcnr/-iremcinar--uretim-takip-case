import createPlotlyComponentImport from 'react-plotly.js/factory';
import PlotlyImport from 'plotly.js/dist/plotly';
import type { PlotParams } from 'react-plotly.js';

function resolveDefault<T>(mod: T | { default: T }): T {
  if (mod && typeof mod === 'object' && 'default' in mod) {
    return (mod as { default: T }).default;
  }
  return mod as T;
}

const createPlotlyComponent = resolveDefault(createPlotlyComponentImport);
const Plotly = resolveDefault(PlotlyImport);
const Plot = createPlotlyComponent(Plotly);

export default function PlotChart(props: PlotParams) {
  return <Plot {...props} />;
}
