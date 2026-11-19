/** Off-screen export: 800×600 at pixel ratio 3 → 2400×1800 px PNG, tagged 300 dpi. */
export const CHART_EXPORT = {
  WIDTH: 800,
  HEIGHT: 600,
  PIXEL_RATIO: 3,
  DPI: 300,
  BACKGROUND: "#ffffff",
} as const;

/** On-screen chart sizes. */
export const CHART_SIZE = {
  /** PCA keeps the legacy 4:3 figure. */
  PCA_ASPECT: 4 / 3,
  /** The network's 600×600 layout box maps to a square plot. */
  NETWORK_ASPECT: 1,
  PCA_SYMBOL_SIZE: 32,
  /** Curveness of each edge of a two-way pair (opposite signs, so the arrows separate). */
  TWO_WAY_CURVENESS: 0.2,
  /** Margin (logical px) around the network layout box. */
  NETWORK_PADDING: 40,
} as const;

export const CHART_TEXT = {
  RESET_VIEW: "Reset view",
  NETWORK_ARIA: (stats: string, layout: string) =>
    `Directed policy network, ${layout} layout. ${stats}`,
  PCA_ARIA: (stats: string, count: number) =>
    `PCA scatter of ${count} policies. ${stats}`,
} as const;
