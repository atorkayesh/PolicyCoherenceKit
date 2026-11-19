import { describe, expect, it } from "vitest";
import {
  crc32,
  dpiToPixelsPerMetre,
  pngChunk,
  withPngDpi,
} from "@/utils/png.utils";

const SIGNATURE = [137, 80, 78, 71, 13, 10, 26, 10];

/** A minimal PNG-shaped byte stream: signature, IHDR, IDAT, IEND. */
function fixturePng(): Uint8Array {
  const parts = [
    Uint8Array.from(SIGNATURE),
    pngChunk("IHDR", new Uint8Array(13)),
    pngChunk("IDAT", Uint8Array.from([1, 2, 3])),
    pngChunk("IEND", new Uint8Array()),
  ];
  const bytes = new Uint8Array(parts.reduce((n, p) => n + p.length, 0));
  let offset = 0;
  for (const part of parts) {
    bytes.set(part, offset);
    offset += part.length;
  }
  return bytes;
}

/** Chunk types in order. */
function chunkTypes(png: Uint8Array): string[] {
  const view = new DataView(png.buffer, png.byteOffset);
  const types: string[] = [];
  let offset = 8;
  while (offset < png.length) {
    const length = view.getUint32(offset);
    types.push(String.fromCharCode(...png.subarray(offset + 4, offset + 8)));
    offset += 12 + length;
  }
  return types;
}

describe("PNG pHYs", () => {
  it("computes the standard CRC-32", () => {
    expect(crc32(new TextEncoder().encode("IEND"))).toBe(0xae426082);
  });

  it("converts 300 dpi to 11811 pixels per metre", () => {
    expect(dpiToPixelsPerMetre(300)).toBe(11811);
  });

  it("inserts one valid pHYs chunk before IDAT", () => {
    const png = withPngDpi(fixturePng(), 300);
    expect(chunkTypes(png)).toEqual(["IHDR", "pHYs", "IDAT", "IEND"]);
    const offset = 8 + 25; // after IHDR (12 + 13)
    const view = new DataView(png.buffer, png.byteOffset);
    expect(view.getUint32(offset)).toBe(9);
    expect(view.getUint32(offset + 8)).toBe(11811);
    expect(view.getUint32(offset + 12)).toBe(11811);
    expect(png[offset + 16]).toBe(1);
    expect(view.getUint32(offset + 17)).toBe(
      crc32(png.subarray(offset + 4, offset + 17)),
    );
    // Running it again replaces the chunk instead of adding a second one.
    expect(chunkTypes(withPngDpi(png, 300))).toEqual([
      "IHDR",
      "pHYs",
      "IDAT",
      "IEND",
    ]);
  });
});
