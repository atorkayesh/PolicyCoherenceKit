import { describe, expect, it } from "vitest";
import { filenameFromDisposition } from "@/utils/content-disposition.utils";

describe("filenameFromDisposition", () => {
  it("prefers the UTF-8 name", () => {
    expect(
      filenameFromDisposition(
        `attachment; filename="Nexus_coherence.xlsx"; filename*=UTF-8''N%C3%A9xus_coherence.xlsx`,
        "x",
      ),
    ).toBe("Néxus_coherence.xlsx");
  });

  it("falls back to the plain name, then to the fallback", () => {
    expect(filenameFromDisposition('attachment; filename="a.xlsx"', "x")).toBe(
      "a.xlsx",
    );
    expect(filenameFromDisposition("attachment; filename=b.xlsx", "x")).toBe(
      "b.xlsx",
    );
    expect(filenameFromDisposition("attachment", "coherence.xlsx")).toBe(
      "coherence.xlsx",
    );
    expect(filenameFromDisposition(null, "coherence.xlsx")).toBe(
      "coherence.xlsx",
    );
  });
});
