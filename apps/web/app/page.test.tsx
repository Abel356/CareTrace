// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import axe from "axe-core";
import { afterEach, expect, it, vi } from "vitest";
import Home from "./page";
import { StatusCard } from "./service-status";

vi.mock("./service-status", async (importOriginal) => {
  const original = await importOriginal<typeof import("./service-status")>();
  return {
    ...original,
    ServiceStatus: () => <original.StatusCard state="ready" />,
  };
});

afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
});

it("renders accessibility landmarks, source abstention, and review guidance", async () => {
  vi.stubEnv("CARETRACE_ENABLE_PUBLIC_IPAC", "false");
  const { container } = render(<Home searchParams={Promise.resolve({})} />);
  expect(screen.getByRole("navigation", { name: "Workspace" })).toBeTruthy();
  expect(screen.getByRole("main")).toBeTruthy();
  expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(
    "IPAC inspection readiness",
  );
  expect(screen.getByText("Insufficient evidence")).toBeTruthy();
  expect(screen.getByText(/qualified legal advice/)).toBeTruthy();
  expect(screen.getByText("Available")).toBeTruthy();
  const report = await axe.run(container, {
    rules: { "color-contrast": { enabled: false } },
  });
  expect(report.violations.map((violation) => violation.id)).toEqual([]);
});

it.each([
  ["development", "false"],
  ["production", "true"],
] as const)(
  "hides citation lookup in %s with the flag set to %s",
  (environment, enabled) => {
    vi.stubEnv("NODE_ENV", environment);
    vi.stubEnv("CARETRACE_ENABLE_PUBLIC_IPAC", enabled);
    render(
      <Home
        searchParams={Promise.resolve({ q: "protocols", as_of: "2025-06-27" })}
      />,
    );
    expect(screen.queryByRole("link", { name: "Citation lookup" })).toBeNull();
    expect(
      screen.queryByRole("heading", { name: "Public IPAC citation lookup" }),
    ).toBeNull();
  },
);

it.each([
  ["checking", "Checking"],
  ["unavailable", "Unavailable"],
] as const)("announces the %s state", (state, label) => {
  render(<StatusCard state={state} />);
  expect(screen.getByRole("status").textContent).toContain(label);
});
