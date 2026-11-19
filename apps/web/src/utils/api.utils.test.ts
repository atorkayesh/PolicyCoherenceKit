import { afterEach, describe, expect, it, vi } from "vitest";
import { z } from "zod";
import { apiResponseSchema } from "@/interfaces/api.interface";
import {
  ApiError,
  apiBlob,
  apiData,
  apiFetch,
  apiFile,
  buildApiUrl,
  errorTitle,
  jsonPost,
  stepError,
} from "@/utils/api.utils";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("buildApiUrl", () => {
  it("prefixes the path with the API origin and /api/v1", () => {
    expect(buildApiUrl("/health", "http://localhost:50002")).toBe(
      "http://localhost:50002/api/v1/health",
    );
  });

  it("builds a relative URL when the origin is empty", () => {
    expect(buildApiUrl("/health", "")).toBe("/api/v1/health");
  });

  it("uses VITE_API_BASE_URL by default", () => {
    expect(buildApiUrl("/health")).toBe("http://localhost:50002/api/v1/health");
  });
});

describe("API calls", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("calls the API URL without credentials", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("{}"));
    vi.stubGlobal("fetch", fetchMock);

    await apiFetch("/scales", { method: "GET" });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:50002/api/v1/scales",
      { method: "GET" },
    );
  });

  it("returns validated data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse({ success: true, data: 3 })),
    );

    await expect(
      apiData("/x", jsonPost({}), apiResponseSchema(z.number())),
    ).resolves.toBe(3);
  });

  it("throws the first field message of a validation error, without Pydantic's prefix", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            success: false,
            message: "Invalid request",
            error: {
              code: "validation_error",
              fields: [
                {
                  field: "policies",
                  message: "Value error, Policy names must be unique.",
                },
              ],
            },
          },
          422,
        ),
      ),
    );

    const error = await apiData(
      "/analysis",
      jsonPost({}),
      apiResponseSchema(z.number()),
    ).catch((caught: unknown) => caught);

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).message).toBe("Policy names must be unique.");
    expect((error as ApiError).status).toBe(422);
  });

  it("throws the public message of an application error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            success: false,
            message: "Expert weights must sum to 1.",
            error: { code: "invalid_weights" },
          },
          422,
        ),
      ),
    );

    await expect(
      apiData("/weights/normalize", jsonPost({}), apiResponseSchema(z.null())),
    ).rejects.toThrow("Expert weights must sum to 1.");
  });

  it("falls back to the status when the body is not JSON", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("oops", { status: 502 })),
    );

    await expect(apiBlob("/x", jsonPost({}))).rejects.toThrow(
      "Request failed (502)",
    );
  });

  it("returns the file of a binary endpoint", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("png")));

    const blob = await apiBlob("/chart", jsonPost({}));

    expect(await blob.text()).toBe("png");
  });

  it("keeps the error code and the feature data (legacy title)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            success: false,
            message: "Please enter a project name.",
            data: { title: "Project Name Required", field: "project_name" },
            error: { code: "invalid_setup", fields: null },
          },
          422,
        ),
      ),
    );
    const error = await apiData(
      "/setup/validate",
      jsonPost({}),
      apiResponseSchema(z.number()),
    ).catch((caught: unknown) => caught);
    expect((error as ApiError).code).toBe("invalid_setup");
    expect((error as ApiError).data).toEqual({
      title: "Project Name Required",
      field: "project_name",
    });
    expect(errorTitle(error)).toBe("Project Name Required");
    expect(stepError(error)).toEqual({
      message: "Please enter a project name.",
      title: "Project Name Required",
      action: undefined,
    });
  });

  it("returns a downloaded file with the name from Content-Disposition", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response("xlsx", {
          headers: {
            "Content-Disposition": `attachment; filename="a.xlsx"; filename*=UTF-8''%C3%A4.xlsx`,
          },
        }),
      ),
    );
    const file = await apiFile(
      "/analysis/export/xlsx",
      jsonPost({}),
      "coherence.xlsx",
    );
    expect(file.filename).toBe("ä.xlsx");
    expect(await file.blob.text()).toBe("xlsx");
  });
});
