import { Fragment, useMemo } from "react";
import { ROLE_TOKENS } from "@/constants/theme.constants";
import type { InsightsData } from "@/interfaces/insights.interface";

/** Escape a string for use inside a regular expression. */
function escapeRegExp(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * The API's story text with each `({code})` coloured by that policy's role (driver, dependent,
 * balanced). Display only: the text is shown verbatim (UI report item 4).
 */
export function StoryText({
  story,
  rows,
}: {
  story: string;
  rows: InsightsData["rows"];
}) {
  const parts = useMemo(() => {
    const roles = new Map(rows.map((row) => [row.code, row.role]));
    if (roles.size === 0) return [story];
    const codes = [...roles.keys()].sort((a, b) => b.length - a.length);
    const pattern = new RegExp(
      `(\\((?:${codes.map(escapeRegExp).join("|")})\\))`,
    );
    return story.split(pattern).map((part) => {
      const code = part.startsWith("(") ? part.slice(1, -1) : null;
      const role = code ? roles.get(code) : undefined;
      return role ? { code: part, role } : part;
    });
  }, [story, rows]);

  return (
    <p className="leading-relaxed whitespace-pre-line">
      {parts.map((part, index) =>
        typeof part === "string" ? (
          // biome-ignore lint/suspicious/noArrayIndexKey: split parts are positional
          <Fragment key={index}>{part}</Fragment>
        ) : (
          <span
            // biome-ignore lint/suspicious/noArrayIndexKey: split parts are positional
            key={index}
            data-role={part.role}
            className={`font-semibold ${ROLE_TOKENS[part.role] ?? ""}`}
          >
            {part.code}
          </span>
        ),
      )}
    </p>
  );
}
