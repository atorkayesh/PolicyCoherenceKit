import { afterEach, describe, expect, it, vi } from "vitest";
import { importWorkbook } from "@/services/import.service";
import { stubJson } from "@/test/fetch";
import { IMPORT_DATA } from "@/test/fixtures/import.fixture";
import { errorBody } from "@/test/fixtures/scales.fixture";
import type { ApiError } from "@/utils/api.utils";

const file = () => new File(["x"], "WEF Nexus Example.xlsx");

describe("import service", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("uploads the file alone for a new project", async () => {
    const fetch = stubJson(IMPORT_DATA);
    await expect(importWorkbook(file())).resolves.toEqual(IMPORT_DATA);
    const [url, init] = fetch.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://localhost:50002/api/v1/imports/workbook");
    const form = init.body as FormData;
    expect((form.get("file") as File).name).toBe("WEF Nexus Example.xlsx");
    expect(form.getAll("policies")).toEqual([]);
    expect(form.getAll("decision_makers")).toEqual([]);
  });

  it("repeats the policies field when importing into the project", async () => {
    const fetch = stubJson(IMPORT_DATA);
    await importWorkbook(file(), ["Energy", "Water"]);
    const form = (fetch.mock.calls[0][1] as RequestInit).body as FormData;
    expect(form.getAll("policies")).toEqual(["Energy", "Water"]);
  });

  it("keeps the warning groups of nothing_imported", async () => {
    const groups = [
      {
        kind: "skipped",
        heading: "The following sheets were skipped:",
        messages: ["S1: empty, skipped"],
      },
    ];
    stubJson(
      errorBody(
        "nothing_imported",
        "No valid matrices were found in the workbook.",
        { warning_groups: groups },
      ),
      422,
      true,
    );
    const error = (await importWorkbook(file()).catch(
      (e: unknown) => e,
    )) as ApiError;
    expect(error.code).toBe("nothing_imported");
    expect(error.data).toEqual({ warning_groups: groups });
  });
});
