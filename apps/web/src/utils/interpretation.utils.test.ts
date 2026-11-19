import { describe, expect, it } from "vitest";
import { headerText, isHeaderLine } from "@/utils/interpretation.utils";

describe("interpretation header rule", () => {
  it("detects ## and numbered 1.–7. lines", () => {
    expect(isHeaderLine("## Overview")).toBe(true);
    expect(isHeaderLine("  3. Influential policies")).toBe(true);
    expect(isHeaderLine("7. Recommendations")).toBe(true);
    expect(isHeaderLine("8. Not a section")).toBe(false);
    expect(isHeaderLine("Plain text")).toBe(false);
  });

  it("strips leading # marks", () => {
    expect(headerText("## 1. Overall")).toBe("1. Overall");
    expect(headerText("2. Synergies")).toBe("2. Synergies");
  });
});
