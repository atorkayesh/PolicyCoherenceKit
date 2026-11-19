/** `filename*=UTF-8''…` (RFC 5987), preferred because it keeps non-ASCII names. */
const EXTENDED = /filename\*\s*=\s*UTF-8''([^;]+)/i;
/** Plain `filename="…"` or `filename=…`. */
const PLAIN = /filename\s*=\s*(?:"([^"]*)"|([^;]+))/i;

/** File name from a `Content-Disposition` header, else `fallback`. */
export function filenameFromDisposition(
  header: string | null,
  fallback: string,
): string {
  if (!header) return fallback;
  const extended = EXTENDED.exec(header);
  if (extended) {
    try {
      return decodeURIComponent(extended[1].trim());
    } catch {
      // Malformed percent-encoding: fall through to the plain name.
    }
  }
  const plain = PLAIN.exec(header);
  const name = (plain?.[1] ?? plain?.[2] ?? "").trim();
  return name || fallback;
}
