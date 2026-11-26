// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import axe from "axe-core";
import { afterEach, expect, it, vi } from "vitest";
import v28 from "../../../corpus/ontario/220246/v28/manifest.json";
import v29 from "../../../corpus/ontario/220246/v29/manifest.json";
import { PublicIpacPanel } from "./public-ipac-panel";

afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

it.each([
  { date: "2025-06-30", snapshot: v28 },
  { date: "2025-07-01", snapshot: v29 },
])(
  "renders exact citations and provenance on $date",
  async ({ date, snapshot }) => {
    vi.stubEnv("CARETRACE_API_ORIGIN", "https://api.example.test");
    const fetchMock = vi.fn().mockResolvedValue(
      Response.json({
        status: "matched",
        corpus: "public_ipac",
        document: snapshot.document,
        version: snapshot.version,
        passages: snapshot.passages.map(
          ({ citation, citation_url, locator }) => ({
            locator,
            citation_url,
            span: citation,
          }),
        ),
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const { container } = render(
      await PublicIpacPanel({
        searchParams: Promise.resolve({ q: "protocols", as_of: date }),
      }),
    );

    expect(fetchMock).toHaveBeenCalledWith(
      new URL(
        `https://api.example.test/api/v1/public/ipac/citations?q=protocols&as_of=${date}`,
      ),
      expect.objectContaining({ cache: "no-store", redirect: "error" }),
    );
    expect(screen.getByText(/small curated historical snapshot/)).toBeTruthy();
    expect(
      screen.getAllByRole("blockquote").map((quote) => quote.textContent),
    ).toEqual(snapshot.passages.map((passage) => passage.citation.quote));
    snapshot.passages.forEach((passage) => {
      expect(
        screen
          .getByRole("link", { name: `Ontario e-Laws, ${passage.locator}` })
          .getAttribute("href"),
      ).toBe(passage.citation_url);
    });
    const { version, effective_from, effective_until } = snapshot.version;
    expect(screen.getByText(/Ontario \(CA-ON\)/).textContent).toBe(
      `Ontario (CA-ON) · ${version} · Effective from ${effective_from} until ${effective_until} (exclusive)`,
    );
    const report = await axe.run(container, {
      rules: { "color-contrast": { enabled: false } },
    });
    expect(report.violations.map((violation) => violation.id)).toEqual([]);
  },
);

it.each([
  [200, { status: "insufficient_evidence" }, /Insufficient evidence/],
  [404, {}, /Citation lookup is unavailable/],
  [200, { status: "matched" }, /Citation lookup is unavailable/],
])(
  "renders the correct status for HTTP %s and %j",
  async (code, body, message) => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(Response.json(body, { status: code })),
    );
    render(
      await PublicIpacPanel({
        searchParams: Promise.resolve({ q: "protocols", as_of: "2025-07-01" }),
      }),
    );
    expect(screen.getByRole("status").textContent).toMatch(message);
    expect(screen.queryByRole("blockquote")).toBeNull();
  },
);
