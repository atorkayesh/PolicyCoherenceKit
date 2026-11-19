/** PNG byte helpers: CRC-32 and the `pHYs` (physical resolution) chunk. */

const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    table[n] = c >>> 0;
  }
  return table;
})();

/** CRC-32 of `bytes` (the PNG chunk checksum over type + data). */
export function crc32(bytes: Uint8Array): number {
  let crc = 0xffffffff;
  for (const byte of bytes) crc = CRC_TABLE[(crc ^ byte) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

/** Pixels per metre for a resolution in dots per inch (300 dpi → 11811). */
export function dpiToPixelsPerMetre(dpi: number): number {
  return Math.round(dpi / 0.0254);
}

const SIGNATURE_LENGTH = 8;

/** One PNG chunk: length, type, data, CRC. */
export function pngChunk(type: string, data: Uint8Array): Uint8Array {
  const chunk = new Uint8Array(12 + data.length);
  const view = new DataView(chunk.buffer);
  view.setUint32(0, data.length);
  for (let i = 0; i < 4; i++) chunk[4 + i] = type.charCodeAt(i);
  chunk.set(data, 8);
  view.setUint32(8 + data.length, crc32(chunk.subarray(4, 8 + data.length)));
  return chunk;
}

/**
 * `png` with a `pHYs` chunk for `dpi` inserted before the first `IDAT` (an existing `pHYs` is
 * dropped), so image programs read the intended print resolution.
 */
export function withPngDpi(png: Uint8Array, dpi: number): Uint8Array {
  const data = new Uint8Array(9);
  const view = new DataView(data.buffer);
  const ppm = dpiToPixelsPerMetre(dpi);
  view.setUint32(0, ppm);
  view.setUint32(4, ppm);
  data[8] = 1; // unit: metre
  const phys = pngChunk("pHYs", data);

  const parts: Uint8Array[] = [png.subarray(0, SIGNATURE_LENGTH)];
  const source = new DataView(png.buffer, png.byteOffset, png.byteLength);
  let offset = SIGNATURE_LENGTH;
  let inserted = false;
  while (offset + 8 <= png.length) {
    const length = source.getUint32(offset);
    const type = String.fromCharCode(...png.subarray(offset + 4, offset + 8));
    const end = offset + 12 + length;
    if (type === "IDAT" && !inserted) {
      parts.push(phys);
      inserted = true;
    }
    if (type !== "pHYs") parts.push(png.subarray(offset, end));
    offset = end;
  }
  const total = parts.reduce((sum, part) => sum + part.length, 0);
  const result = new Uint8Array(total);
  let position = 0;
  for (const part of parts) {
    result.set(part, position);
    position += part.length;
  }
  return result;
}

/** Bytes of a base64 `data:` URL. */
export function dataUrlToBytes(dataUrl: string): Uint8Array {
  const base64 = dataUrl.slice(dataUrl.indexOf(",") + 1);
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}
