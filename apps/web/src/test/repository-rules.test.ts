// @vitest-environment node
import { readdirSync, readFileSync } from "node:fs";
import { join, relative, sep } from "node:path";
import { describe, expect, it } from "vitest";

/** `apps/web`, from `src/test`. */
const ROOT = join(import.meta.dirname, "..", "..");
const SKIP_DIRS = new Set([
  "node_modules",
  ".output",
  ".nitro",
  ".tanstack",
  "dist",
  "coverage",
  "public",
]);
const SKIP_FILES = new Set(["src/routeTree.gen.ts"]);
const CODE = /\.(ts|tsx|js|mjs|css)$/;
const MAX_LINES = 300;
const SELF = "src/test/repository-rules.test.ts";
/** Built so this file does not contain the forbidden literal itself. */
const LEGACY_DIR = ["tk", "app"].join("-");

function codeFiles(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    if (entry.isDirectory())
      return SKIP_DIRS.has(entry.name) ? [] : codeFiles(path);
    const name = relative(ROOT, path).split(sep).join("/");
    return CODE.test(entry.name) && !SKIP_FILES.has(name) ? [name] : [];
  });
}

const files = codeFiles(ROOT);

describe("repository rules", () => {
  it("finds the code files", () => {
    expect(files).toContain("src/router.tsx");
    expect(files).toContain("vite.config.ts");
  });

  it("keeps every code file at 300 lines or fewer", () => {
    const tooLong = files
      .map((file) => ({
        file,
        lines: readFileSync(join(ROOT, file), "utf8").split("\n").length,
      }))
      .filter(({ lines }) => lines > MAX_LINES);
    expect(tooLong).toEqual([]);
  });

  it("never references the legacy app directory", () => {
    const offending = files.filter(
      (file) =>
        file !== SELF &&
        readFileSync(join(ROOT, file), "utf8").includes(LEGACY_DIR),
    );
    expect(offending).toEqual([]);
  });
});
