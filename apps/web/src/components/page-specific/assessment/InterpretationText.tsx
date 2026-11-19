import { EXPLANATION_TEXT } from "@/constants/explanation.constants";
import { headerText, isHeaderLine } from "@/utils/interpretation.utils";

/**
 * The interpretation: section header lines (`##…`, `1.`–`7.`) as bold ink lines without `#`,
 * other lines as plain text (llm_tab.py:860-875 rule).
 */
export function InterpretationText({ text }: { text: string }) {
  // Lines are positional: their number is the key.
  const lines = (text ? text.split(/\r?\n/) : []).map((line, number) => ({
    line,
    key: `line-${number}`,
  }));
  return (
    <div className="flex flex-col gap-1">
      <p className="text-sm font-semibold">{EXPLANATION_TEXT.OUTPUT_LABEL}</p>
      <output
        aria-label={EXPLANATION_TEXT.OUTPUT_LABEL}
        className="block min-h-40 rounded-lg border bg-card p-3 text-sm wrap-break-word"
      >
        {lines.map(({ line, key }) =>
          isHeaderLine(line) ? (
            <strong
              key={key}
              className="block pt-1 font-semibold text-foreground"
            >
              {headerText(line)}
            </strong>
          ) : (
            <span key={key} className="block min-h-[1lh] whitespace-pre-wrap">
              {line}
            </span>
          ),
        )}
      </output>
    </div>
  );
}
