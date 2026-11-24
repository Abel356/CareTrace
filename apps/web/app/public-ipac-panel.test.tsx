// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import axe from "axe-core";
import { afterEach, expect, it, vi } from "vitest";
import snapshot from "../../../corpus/ontario/220246/v28/manifest.json";
import { PublicIpacPanel } from "./public-ipac-panel";

afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

it("renders the exact verified quote and provenance for the selected date", async () => {
  vi.stubEnv("CARETRACE_API_ORIGIN", "https://api.example.test");
  const fetchMock = vi.fn().mockResolvedValue(
    Response.json({
      status: "matched",
      corpus: "public_ipac",
      document: snapshot.document,
      version: snapshot.version,
      passages: [
        {
          locator: snapshot.locator,
          citation_url: snapshot.citation_url,
          span: snapshot.citation,
        },
      ],
    }),
  );
  vi.stubGlobal("fetch", fetchMock);

  const { container } = render(
    await PublicIpacPanel({
      searchParams: Promise.resolve({ q: "protocols", as_of: "2025-06-27" }),
    }),
  );

  expect(fetchMock).toHaveBeenCalledWith(
    new URL(
      "https://api.example.test/api/v1/public/ipac/citations?q=protocols&as_of=2025-06-27",
    ),
    expect.objectContaining({ cache: "no-store", redirect: "error" }),
  );
  expect(screen.getByRole("blockquote").textContent).toBe(
    snapshot.citation.quote,
  );
  expect(
    screen.getByRole("link", { name: /s\. 102 \(3\)/ }).getAttribute("href"),
  ).toBe(snapshot.citation_url);
  expect(screen.getByText(/Ontario \(CA-ON\) · v28/).textContent).toContain(
    "2025-06-27 until 2025-07-01 (exclusive)",
  );
  const report = await axe.run(container, {
    rules: { "color-contrast": { enabled: false } },
  });
  expect(report.violations.map((violation) => violation.id)).toEqual([]);
});
