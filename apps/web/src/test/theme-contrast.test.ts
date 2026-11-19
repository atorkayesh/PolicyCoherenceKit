// @vitest-environment node
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { contrastRatio, rootTokens } from "@/test/contrast";
import { SCALES } from "@/test/fixtures/scales.fixture";

const css = readFileSync(join(import.meta.dirname, "..", "styles.css"), "utf8");
const tokens = rootTokens(css);
const token = (name: string) => tokens.get(name) ?? "";

/** The Theme table: token, web fill/text, and whether the legacy pair is kept unchanged. */
const PAIRS: [string, string, string, number][] = [
  ["rating-indivisible", "#0b6e6e", "#ffffff", 6.05],
  ["rating-reinforcing", "#238377", "#ffffff", 4.58],
  ["rating-enabling", "#6baf92", "#2d2d2d", 5.36],
  ["rating-neutral", "#b0b7c3", "#484848", 4.53],
  ["rating-constraining", "#e9c46a", "#2d2d2d", 8.24],
  ["rating-counteracting", "#d6421d", "#ffffff", 4.51],
  ["rating-cancelling", "#9b2226", "#ffffff", 7.92],
  ["value-strong-positive", "#177e40", "#ffffff", 5.13],
  ["value-positive", "#25c263", "#2d2d2d", 5.89],
  ["value-weak-positive", "#88edaf", "#2d2d2d", 9.69],
  ["value-zero", "#d9d9d9", "#555555", 5.28],
  ["value-weak-negative", "#f5c07a", "#2d2d2d", 8.33],
  ["value-negative", "#e07b39", "#2d2d2d", 4.63],
  ["value-strong-negative", "#eb1515", "#ffffff", 4.52],
  ["count-very-high", "#7799b9", "#2d2d2d", 4.62],
  ["count-high", "#a6bcd3", "#1f2937", 7.52],
  ["count-medium", "#d0dbe7", "#1f2937", 10.46],
  ["count-low", "#eae7e0", "#666666", 4.65],
  ["count-none", "#d9d9d9", "#555555", 5.28],
  ["entropy-low", "#a3a3a3", "#2d2d2d", 5.46],
  ["entropy-low-to-medium", "#a7f3d0", "#2d2d2d", 10.74],
  ["entropy-medium-to-high", "#34d399", "#2d2d2d", 7.16],
  ["entropy-high", "#05875f", "#ffffff", 4.53],
];

/** Legacy colours from `/scales` (fixture), keyed like the tokens. */
const LEGACY = new Map<string, { fill: string; text: string }>([
  ...SCALES.ratings.map((r) => [`rating-${r.label.toLowerCase()}`, r] as const),
  ...SCALES.value_bands.map(
    (b) => [`value-${b.key.replaceAll("_", "-")}`, b] as const,
  ),
  ...SCALES.count_bands.map(
    (b) => [`count-${b.key.replaceAll("_", "-")}`, b] as const,
  ),
  ...SCALES.entropy_categories.map(
    (c) => [`entropy-${c.label.toLowerCase()}`, c] as const,
  ),
]);

describe("theme contrast (WCAG AA)", () => {
  it.each(
    PAIRS,
  )("%s matches the Theme table and reaches 4.5:1", (name, fill, text, ratio) => {
    expect(token(name)).toBe(fill);
    expect(token(`${name}-foreground`)).toBe(text);
    const measured = contrastRatio(fill, text);
    expect(measured).toBeGreaterThanOrEqual(4.5);
    expect(measured).toBeCloseTo(ratio, 2);
  });

  it("keeps the legacy colours of unchanged pairs", () => {
    for (const [name, fill, text, ratio] of PAIRS) {
      const legacy = LEGACY.get(name);
      expect(legacy, name).toBeDefined();
      const legacyRatio = contrastRatio(legacy?.fill ?? "", legacy?.text ?? "");
      if (Math.abs(legacyRatio - ratio) < 0.005) {
        expect(fill, name).toBe(legacy?.fill.toLowerCase());
        expect(text, name).toBe(legacy?.text.toLowerCase());
      }
    }
  });

  it.each([
    ["foreground", "card", 10.98],
    ["foreground", "background", 10.52],
    ["foreground", "muted", 9.89],
    ["muted-foreground", "card", 5.29],
    ["muted-foreground", "background", 5.07],
    ["muted-foreground", "muted", 4.77],
  ])("base %s on %s reaches AA", (text, surface, ratio) => {
    const measured = contrastRatio(token(text), token(surface));
    expect(measured).toBeGreaterThanOrEqual(4.5);
    expect(measured).toBeCloseTo(ratio, 1);
  });

  it.each([
    ["role-driver", 4.51],
    ["role-dependent", 4.6],
    ["role-balanced", 4.76],
  ])("story role ink %s reaches AA on the card", (name, ratio) => {
    const measured = contrastRatio(token(name), token("card"));
    expect(measured).toBeGreaterThanOrEqual(4.5);
    expect(measured).toBeCloseTo(ratio, 1);
  });
});
