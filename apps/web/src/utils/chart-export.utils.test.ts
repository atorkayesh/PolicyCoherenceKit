import { afterEach, describe, expect, it, vi } from "vitest";
import {
  chartFileName,
  downloadChart,
  exportOption,
} from "@/utils/chart-export.utils";
import { saveBlob } from "@/utils/download.utils";
import { pngChunk } from "@/utils/png.utils";

const fake = vi.hoisted(() => ({
  init: vi.fn(),
  setOption: vi.fn(),
  dispose: vi.fn(),
  getDataURL: vi.fn(),
  renderToSVGString: vi.fn(() => "<svg>P1</svg>"),
}));

vi.mock("@/utils/echarts.utils", () => ({
  echarts: {
    init: (...args: unknown[]) => {
      fake.init(...args);
      return fake;
    },
  },
}));
vi.mock("@/utils/download.utils", () => ({ saveBlob: vi.fn() }));

function pngDataUrl(): string {
  const parts = [
    Uint8Array.from([137, 80, 78, 71, 13, 10, 26, 10]),
    pngChunk("IHDR", new Uint8Array(13)),
    pngChunk("IDAT", new Uint8Array(2)),
    pngChunk("IEND", new Uint8Array()),
  ];
  const bytes = parts.flatMap((p) => Array.from(p));
  return `data:image/png;base64,${btoa(String.fromCharCode(...bytes))}`;
}

describe("chart downloads", () => {
  afterEach(() => vi.clearAllMocks());

  it("names files like the legacy app", () => {
    expect(chartFileName("network_plot", "png")).toBe("network_plot.png");
    expect(chartFileName("pca_plot", "svg")).toBe("pca_plot.svg");
    expect(exportOption({ animation: true })).toEqual({
      animation: false,
      backgroundColor: "#ffffff",
    });
  });

  it("renders a 2400×1800 PNG off-screen with a 300 dpi pHYs chunk", async () => {
    fake.getDataURL.mockReturnValue(pngDataUrl());
    await downloadChart({ series: [] }, "png", "network_plot");
    expect(fake.init.mock.calls[0][2]).toMatchObject({
      renderer: "canvas",
      width: 800,
      height: 600,
    });
    expect(fake.getDataURL).toHaveBeenCalledWith(
      expect.objectContaining({
        type: "png",
        pixelRatio: 3,
        backgroundColor: "#ffffff",
      }),
    );
    expect(fake.dispose).toHaveBeenCalled();
    const [blob, name] = vi.mocked(saveBlob).mock.calls[0];
    expect(name).toBe("network_plot.png");
    const bytes = new Uint8Array(await blob.arrayBuffer());
    expect(String.fromCharCode(...bytes.subarray(37, 41))).toBe("pHYs");
  });

  it("renders SVG with the server-side SVG renderer", async () => {
    await downloadChart({ series: [] }, "svg", "pca_plot");
    expect(fake.init).toHaveBeenCalledWith(
      null,
      null,
      expect.objectContaining({ renderer: "svg", ssr: true }),
    );
    const [blob, name] = vi.mocked(saveBlob).mock.calls[0];
    expect(name).toBe("pca_plot.svg");
    expect(await blob.text()).toBe("<svg>P1</svg>");
  });
});
