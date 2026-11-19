/**
 * Display formatting of API numbers, like Python's `format` at the same precision. The API already
 * rounds every number to its display precision, so these never re-round beyond it.
 */

/** Whether `value` is negative zero (`JSON.parse("-0.0")` keeps the sign). */
function isNegativeZero(value: number): boolean {
  return value === 0 && Object.is(value, -0);
}

/** Like `f"{value:.{digits}f}"`: `-0.0` → `-0.00`. */
export function formatFixed(value: number, digits: number): string {
  const text = value.toFixed(digits);
  return isNegativeZero(value) && !text.startsWith("-") ? `-${text}` : text;
}

/** Like `f"{value:+.{digits}f}"`: `0.0` → `+0.00`, `-0.0` → `-0.00`. */
export function formatSigned(value: number, digits: number): string {
  const text = formatFixed(value, digits);
  return text.startsWith("-") ? text : `+${text}`;
}

/** Like `str(float(value))`: `42.0` → `"42.0"`, `0.123` → `"0.123"`, `-0.0` → `"-0.0"`. */
export function pyFloatStr(value: number): string {
  if (isNegativeZero(value)) return "-0.0";
  if (!Number.isFinite(value)) {
    if (Number.isNaN(value)) return "nan";
    return value > 0 ? "inf" : "-inf";
  }
  const magnitude = Math.abs(value);
  if (magnitude !== 0 && (magnitude < 1e-4 || magnitude >= 1e16)) {
    // repr() switches to exponent notation here, with at least two exponent digits.
    return value.toExponential().replace(/e([+-])(\d)$/, "e$10$2");
  }
  const text = String(value);
  return Number.isInteger(value) ? `${text}.0` : text;
}

/** An integer count (an API float like `3.0` shows as `3`). */
export function formatInt(value: number): string {
  return String(Math.trunc(value));
}

/** `decision-maker` for 1, `decision-makers` otherwise (owner decision 2026-11-18). */
export function decisionMakerWord(count: number): string {
  return count === 1 ? "decision-maker" : "decision-makers";
}
