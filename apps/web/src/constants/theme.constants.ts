/**
 * Token classes per API key (rating labels, band keys, entropy category labels, roles). The class
 * names are written out in full so Tailwind generates them.
 */
export const RATING_TOKENS: Record<string, string> = {
  Indivisible: "bg-rating-indivisible text-rating-indivisible-foreground",
  Reinforcing: "bg-rating-reinforcing text-rating-reinforcing-foreground",
  Enabling: "bg-rating-enabling text-rating-enabling-foreground",
  Neutral: "bg-rating-neutral text-rating-neutral-foreground",
  Constraining: "bg-rating-constraining text-rating-constraining-foreground",
  Counteracting: "bg-rating-counteracting text-rating-counteracting-foreground",
  Cancelling: "bg-rating-cancelling text-rating-cancelling-foreground",
};

export const VALUE_BAND_TOKENS: Record<string, string> = {
  strong_positive:
    "bg-value-strong-positive text-value-strong-positive-foreground",
  positive: "bg-value-positive text-value-positive-foreground",
  weak_positive: "bg-value-weak-positive text-value-weak-positive-foreground",
  zero: "bg-value-zero text-value-zero-foreground",
  weak_negative: "bg-value-weak-negative text-value-weak-negative-foreground",
  negative: "bg-value-negative text-value-negative-foreground",
  strong_negative:
    "bg-value-strong-negative text-value-strong-negative-foreground",
};

export const COUNT_BAND_TOKENS: Record<string, string> = {
  very_high: "bg-count-very-high text-count-very-high-foreground",
  high: "bg-count-high text-count-high-foreground",
  medium: "bg-count-medium text-count-medium-foreground",
  low: "bg-count-low text-count-low-foreground",
  none: "bg-count-none text-count-none-foreground",
};

export const ENTROPY_TOKENS: Record<string, string> = {
  Low: "bg-entropy-low text-entropy-low-foreground",
  "Low-to-Medium":
    "bg-entropy-low-to-medium text-entropy-low-to-medium-foreground",
  "Medium-to-High":
    "bg-entropy-medium-to-high text-entropy-medium-to-high-foreground",
  High: "bg-entropy-high text-entropy-high-foreground",
};

export const ROLE_TOKENS: Record<string, string> = {
  driver: "text-role-driver",
  dependent: "text-role-dependent",
  balanced: "text-role-balanced",
};

/** Fallback for a key the theme does not know (never expected; keeps the text readable). */
export const UNKNOWN_TOKEN = "bg-muted text-foreground";

/** Token classes for `key` in `tokens`, or the neutral fallback. */
export function tokenFor(tokens: Record<string, string>, key: string): string {
  return tokens[key] ?? UNKNOWN_TOKEN;
}
