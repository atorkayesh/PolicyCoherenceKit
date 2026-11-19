import { afterEach, describe, expect, it, vi } from "vitest";
import { exportXlsx } from "@/services/export.service";
import { sentRequest } from "@/test/fetch";
import { REQUEST } from "@/test/fixtures/request.fixture";

describe("export service", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("downloads the XLSX under the API's file name, else the fallback", async () => {
    const fetch = vi.fn().mockResolvedValueOnce(
      new Response("x", {
        headers: {
          "Content-Disposition": `attachment; filename="Nexus_coherence.xlsx"`,
        },
      }),
    );
    vi.stubGlobal("fetch", fetch);
    expect((await exportXlsx(REQUEST)).filename).toBe("Nexus_coherence.xlsx");
    expect(sentRequest(fetch)).toMatchObject({
      url: "http://localhost:50002/api/v1/analysis/export/xlsx",
      body: REQUEST,
    });
    fetch.mockResolvedValueOnce(new Response("x"));
    expect((await exportXlsx(REQUEST)).filename).toBe("coherence.xlsx");
  });
});
