declare module 'react-plotly.js' {
  import type { FC, CSSProperties } from 'react';
  import type { Config, Data, Layout } from 'plotly.js';

  export interface PlotParams {
    data: Data[];
    layout?: Partial<Layout>;
    config?: Partial<Config>;
    style?: CSSProperties;
    className?: string;
    useResizeHandler?: boolean;
    onInitialized?: (figure: unknown, graphDiv: unknown) => void;
    onUpdate?: (figure: unknown, graphDiv: unknown) => void;
  }

  const Plot: FC<PlotParams>;
  export default Plot;
}

declare module 'react-plotly.js/factory' {
  import type { FC } from 'react';
  import type { PlotParams } from 'react-plotly.js';

  export default function createPlotlyComponent(plotly: unknown): FC<PlotParams>;
}

declare module 'plotly.js/dist/plotly' {
  const Plotly: unknown;
  export default Plotly;
}
