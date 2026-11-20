import { afterEach, describe, expect, it, vi } from "vitest";
import { getReadiness } from "./readiness";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("getReadiness", () => {
  it("requests the typed readiness path on the configured origin", async () => {
    vi.stubEnv("CARETRACE_API_ORIGIN", "https://api.example.test");
    const fetchMock = vi
      .fn()
      .mockResolvedValue(Response.json({ status: "ready" }));
    vi.stubGlobal("fetch", fetchMock);
    await expect(getReadiness()).resolves.toBe("ready");
    expect(fetchMock).toHaveBeenCalledWith(
      new URL("https://api.example.test/readyz"),
      expect.objectContaining({ cache: "no-store", redirect: "error" }),
    );
  });

  it.each([
    { status: "unavailable", code: 503 },
    { status: "unknown", code: 200 },
  ])(
    "abstains with status $status and HTTP $code",
    async ({ status, code }) => {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue(Response.json({ status }, { status: code })),
      );
      await expect(getReadiness()).resolves.toBe("unavailable");
    },
  );

  it("handles connection errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("synthetic connection failure")),
    );
    await expect(getReadiness()).resolves.toBe("unavailable");
  });
});
