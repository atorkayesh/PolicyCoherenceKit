/** WCAG 2.x contrast helpers (test only). */

function channel(value: number): number {
  const c = value / 255;
  return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

/** Relative luminance of a `#rrggbb` colour. */
export function luminance(hex: string): number {
  const value = hex.replace("#", "");
  const [r, g, b] = [0, 2, 4].map((i) =>
    Number.parseInt(value.slice(i, i + 2), 16),
  );
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
}

/** Contrast ratio of two colours (1 to 21). */
export function contrastRatio(a: string, b: string): number {
  const [light, dark] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (light + 0.05) / (dark + 0.05);
}

/** `--name: value;` declarations of the `:root` block of a stylesheet. */
export function rootTokens(css: string): Map<string, string> {
  const start = css.indexOf(":root {");
  const block = css.slice(start, css.indexOf("}", start));
  const tokens = new Map<string, string>();
  for (const match of block.matchAll(/--([\w-]+):\s*([^;]+);/g)) {
    tokens.set(match[1], match[2].trim().toLowerCase());
  }
  return tokens;
}
