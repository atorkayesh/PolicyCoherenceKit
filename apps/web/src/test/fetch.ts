import { vi } from "vitest";
import { envelope } from "@/test/fixtures/scales.fixture";

/** Stub `fetch` with one JSON response (the data is wrapped in the API envelope). */
export function stubJson(data: unknown, status = 200, raw = false) {
  const fetch = vi.fn().mockResolvedValue(
    new Response(JSON.stringify(raw ? data : envelope(data)), {
      status,
      headers: { "Content-Type": "application/json" },
    }),
  );
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

/** URL, method and parsed JSON body of the stubbed call `index`. */
export function sentRequest(fetch: ReturnType<typeof vi.fn>, index = 0) {
  const [url, init] = fetch.mock.calls[index] as [string, RequestInit];
  const body =
    typeof init.body === "string" ? JSON.parse(init.body) : init.body;
  return { url, method: init.method ?? "GET", body };
}
