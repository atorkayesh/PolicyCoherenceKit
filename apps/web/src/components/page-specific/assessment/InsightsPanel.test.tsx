import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { InsightsPanel } from "@/components/page-specific/assessment/InsightsPanel";
import { ANALYSIS } from "@/test/fixtures/analysis.fixture";

describe("InsightsPanel", () => {
  it("colours each (code) of the story by the policy's role", () => {
    render(<InsightsPanel data={ANALYSIS} />);
    const codes = Array.from(document.querySelectorAll("[data-role]"));
    expect(
      codes.map((el) => [el.textContent, el.getAttribute("data-role")]),
    ).toEqual([
      ["(P1)", "driver"],
      ["(P2)", "dependent"],
      ["(P1)", "driver"],
      ["(P2)", "dependent"],
      ["(P3)", "balanced"],
    ]);
    expect(codes[0].className).toContain("text-role-driver");
    expect(screen.getByText(/drives Water/).textContent).toBe(
      ANALYSIS.insights.texts.story,
    );
  });

  it("shows the API texts on every card", () => {
    render(<InsightsPanel data={ANALYSIS} />);
    for (const text of [
      "Key Insights",
      "Interpretation:",
      "Top Driving Policy: Energy (P1)",
      "Strongest Link: Food (P3) → Water (P2)",
      "Analysis Overview",
      "Decision-maker agreement",
      "Average rank agreement between decision-makers (0 to 1).",
      "0.75",
      "System Health",
      "Top Influenced Policy",
      "+4.50 WII",
      "+3.00 positive link",
      "Water (P2) ↔ Energy (P1)",
      "Rating agreement: 0.50",
      "Rating agreement is the share of decision-makers giving the most common rating.",
      "Conflict Ratio",
      "25%",
      "1 of 4 active links",
    ]) {
      expect(screen.getAllByText(text).length, text).toBeGreaterThan(0);
    }
  });

  it("shows health shares with % and a minimum bar width", () => {
    render(<InsightsPanel data={ANALYSIS} />);
    expect(screen.getByText("50%")).toBeDefined();
    expect(screen.getByText("0%")).toBeDefined();
    const neutral = screen.getByText("Neutral/Uncertain").nextElementSibling
      ?.firstElementChild as HTMLElement;
    expect(neutral.style.width).toBe("3%");
    expect(neutral.className).toContain("bg-health-neutral");
  });
});
