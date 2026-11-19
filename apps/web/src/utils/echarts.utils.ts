/**
 * Tree-shaken ECharts: only the graph and scatter charts, the components they use and both
 * renderers. Imported lazily (dynamic `import()`) by the chart components, never at module scope of
 * a route, so the chart chunk is loaded only when a chart or a chart download is needed.
 */
import { GraphChart, ScatterChart } from "echarts/charts";
import {
  AriaComponent,
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  TitleComponent,
  TooltipComponent,
} from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer, SVGRenderer } from "echarts/renderers";

echarts.use([
  GraphChart,
  ScatterChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  MarkLineComponent,
  TitleComponent,
  AriaComponent,
  CanvasRenderer,
  SVGRenderer,
]);

export { echarts };
