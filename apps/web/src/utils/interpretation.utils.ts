/** A line rendered as a heading: `##…` or a numbered section `1.`–`7.` (llm_tab.py:860-875). */
export function isHeaderLine(line: string): boolean {
  const text = line.trim();
  return text.startsWith("##") || /^[1-7]\./.test(text);
}

/** A heading line without its leading `#` marks. */
export function headerText(line: string): string {
  return line.trim().replace(/^#+\s*/, "");
}
