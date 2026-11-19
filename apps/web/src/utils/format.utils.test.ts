import { describe, expect, it } from "vitest";
import {
  decisionMakerWord,
  formatFixed,
  formatInt,
  formatSigned,
  pyFloatStr,
} from "@/utils/format.utils";

describe("format utils (Python-compatible)", () => {
  it("formats fixed digits, keeping negative zero", () => {
    expect(formatFixed(1.5, 2)).toBe("1.50");
    expect(formatFixed(-0, 2)).toBe("-0.00");
    expect(formatFixed(JSON.parse("-0.0"), 2)).toBe("-0.00");
    expect(formatFixed(0.9183, 4)).toBe("0.9183");
    expect(formatFixed(1, 4)).toBe("1.0000");
  });

  it("formats signed values like +.2f", () => {
    expect(formatSigned(0, 2)).toBe("+0.00");
    expect(formatSigned(-0, 2)).toBe("-0.00");
    expect(formatSigned(1.5, 2)).toBe("+1.50");
    expect(formatSigned(-2.25, 2)).toBe("-2.25");
    expect(formatSigned(2, 0)).toBe("+2");
  });

  it("writes floats like str(float)", () => {
    expect(pyFloatStr(42)).toBe("42.0");
    expect(pyFloatStr(0.123)).toBe("0.123");
    expect(pyFloatStr(0)).toBe("0.0");
    expect(pyFloatStr(-0)).toBe("-0.0");
    expect(pyFloatStr(0.01)).toBe("0.01");
    expect(pyFloatStr(1e-5)).toBe("1e-05");
    expect(pyFloatStr(1e16)).toBe("1e+16");
  });

  it("formats integer counts and the decision-maker word", () => {
    expect(formatInt(3)).toBe("3");
    expect(decisionMakerWord(1)).toBe("decision-maker");
    expect(decisionMakerWord(2)).toBe("decision-makers");
    expect(decisionMakerWord(0)).toBe("decision-makers");
  });
});
