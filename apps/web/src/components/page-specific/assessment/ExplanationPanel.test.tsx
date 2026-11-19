import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { toast } from "sonner";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ExplanationPanel } from "@/components/page-specific/assessment/ExplanationPanel";
import { InterpretationText } from "@/components/page-specific/assessment/InterpretationText";
import {
  explain,
  getExplanationProviders,
} from "@/services/explanation.service";
import { useProjectStore } from "@/store/project.store";
import { INTERPRETATION, PROVIDERS } from "@/test/fixtures/explanation.fixture";
import { REQUEST } from "@/test/fixtures/request.fixture";
import { renderWithQuery } from "@/test/render";
import { pickOption } from "@/test/select";
import { ApiError } from "@/utils/api.utils";

vi.mock("@/services/explanation.service", () => ({
  explain: vi.fn(),
  getExplanationProviders: vi.fn(),
}));
vi.mock("sonner", () => ({ toast: { error: vi.fn() } }));

const KEY = "sk-secret-key-123";
const keyInput = () => screen.getByLabelText("API Key") as HTMLInputElement;
const setKey = () => fireEvent.change(keyInput(), { target: { value: KEY } });
const generateButton = () =>
  screen.getByRole("button", { name: /Generate Interpretation|Generating/ });
const generate = () => fireEvent.click(generateButton());
const providerSelect = () => screen.findByLabelText("AI Provider");

async function renderPanel() {
  const result = renderWithQuery(<ExplanationPanel snapshot={REQUEST} />);
  await providerSelect();
  return result;
}

describe("ExplanationPanel", () => {
  beforeEach(() => {
    vi.mocked(explain).mockReset();
    vi.mocked(toast.error).mockReset();
    vi.mocked(getExplanationProviders).mockResolvedValue(PROVIDERS);
    useProjectStore.getState().reset();
  });

  it("shows the texts and asks for a key before sending anything", async () => {
    await renderPanel();
    expect(screen.getByText("AI Interpretation")).toBeDefined();
    expect(
      screen.getByText(
        /sent through our server to the AI provider for this request only/,
      ),
    ).toBeDefined();
    generate();
    expect(screen.getByRole("alert").textContent).toBe(
      "API Key RequiredPlease enter your API key before generating.",
    );
    expect(explain).not.toHaveBeenCalled();
  });

  it("hides the key until the eye button is pressed", async () => {
    await renderPanel();
    expect(keyInput().type).toBe("password");
    fireEvent.click(screen.getByRole("button", { name: "Show API key" }));
    expect(keyInput().type).toBe("text");
  });

  it("resets the model when the provider changes", async () => {
    await renderPanel();
    await pickOption(screen.getByLabelText("Model"), "llama-3.3-70b");
    await pickOption(await providerSelect(), "OpenAI");
    expect(screen.getByLabelText("Model").textContent).toContain("gpt-4o-mini");
  });

  it("blocks Generate for Azure until a deployment is typed", async () => {
    vi.mocked(explain).mockResolvedValue({
      text: "T",
      provider: "azure_openai",
      model: "dep",
    });
    await renderPanel();
    await pickOption(await providerSelect(), "Azure OpenAI");
    setKey();
    expect((generateButton() as HTMLButtonElement).disabled).toBe(true);
    fireEvent.change(screen.getByLabelText("Model"), {
      target: { value: "dep" },
    });
    expect((generateButton() as HTMLButtonElement).disabled).toBe(false);
    generate();
    fireEvent.change(
      await screen.findByRole("textbox", { name: "Azure OpenAI Endpoint" }),
      {
        target: { value: " https://x.openai.azure.com " },
      },
    );
    fireEvent.click(screen.getByRole("button", { name: "OK" }));
    await waitFor(() => expect(explain).toHaveBeenCalledOnce());
    expect(vi.mocked(explain).mock.calls[0][0].azure_endpoint).toBe(
      "https://x.openai.azure.com",
    );
  });

  it("uses the snapshot, stores the text, clears the key, and never keeps the key", async () => {
    vi.mocked(explain).mockResolvedValue({
      text: INTERPRETATION,
      provider: "groq",
      model: "llama-3.1-8b",
    });
    const { queryClient } = await renderPanel();
    setKey();
    generate();
    expect(screen.getByText("Calling Groq / llama-3.1-8b ...")).toBeDefined();
    expect(await screen.findByText("Done.")).toBeDefined();
    expect(vi.mocked(explain).mock.calls[0][0]).toMatchObject({
      analysis: REQUEST,
      provider: "groq",
      api_key: KEY,
    });
    expect(keyInput().value).toBe("");
    expect(useProjectStore.getState().interpretationText).toBe(INTERPRETATION);
    expect(JSON.stringify(useProjectStore.getState())).not.toContain(KEY);
    const cached = JSON.stringify([
      queryClient
        .getQueryCache()
        .getAll()
        .map((q) => [q.queryKey, q.state]),
      queryClient
        .getMutationCache()
        .getAll()
        .map((m) => [m.options.mutationKey, m.state]),
    ]);
    expect(cached).not.toContain(KEY);
  });

  it("clears the key and the old text on failure, with a toast", async () => {
    useProjectStore.getState().setInterpretationText("Old");
    vi.mocked(explain).mockRejectedValue(
      new ApiError("The AI provider rejected the API key.", 502),
    );
    await renderPanel();
    setKey();
    generate();
    expect(await screen.findByText("Error.")).toBeDefined();
    expect(toast.error).toHaveBeenCalledWith("The request failed", {
      description: "The AI provider rejected the API key.",
    });
    expect(keyInput().value).toBe("");
    expect(useProjectStore.getState().interpretationText).toBe("");
  });
});

describe("InterpretationText", () => {
  it("renders header lines bold without # and other lines plain", () => {
    render(<InterpretationText text={INTERPRETATION} />);
    const bold = Array.from(document.querySelectorAll("strong")).map(
      (el) => el.textContent,
    );
    expect(bold).toEqual(["1. Overall coherence", "2. Key synergies"]);
    expect(screen.getByText("Energy & water.").tagName).toBe("SPAN");
  });
});
