import { afterEach, describe, expect, it, vi } from "vitest";
import {
  explain,
  exportInterpretationPdf,
  getExplanationProviders,
} from "@/services/explanation.service";
import { sentRequest, stubJson } from "@/test/fetch";
import { PROVIDERS } from "@/test/fixtures/explanation.fixture";
import { REQUEST } from "@/test/fixtures/request.fixture";

describe("explanation service", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("lists the providers", async () => {
    stubJson({ providers: PROVIDERS });
    await expect(getExplanationProviders()).resolves.toEqual(PROVIDERS);
  });

  it("sends the key only in the body", async () => {
    const fetch = stubJson({ text: "T", provider: "groq", model: "m" });
    await explain({
      analysis: REQUEST,
      provider: "groq",
      api_key: "secret",
      model: "m",
    });
    const sent = sentRequest(fetch);
    expect(sent.url).toBe("http://localhost:50002/api/v1/explanations");
    expect(sent.url).not.toContain("secret");
    expect(sent.body.api_key).toBe("secret");
  });

  it("downloads the interpretation PDF", async () => {
    const fetch = vi.fn().mockResolvedValue(new Response("%PDF"));
    vi.stubGlobal("fetch", fetch);
    const file = await exportInterpretationPdf("Text");
    expect(file.filename).toBe("policy_interpretation.pdf");
    expect(sentRequest(fetch)).toMatchObject({
      url: "http://localhost:50002/api/v1/explanations/export/pdf",
      body: { text: "Text" },
    });
  });
});
