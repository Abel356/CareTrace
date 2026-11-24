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

afterEach(cleanup);

it("renders accessibility landmarks, source abstention, and review guidance", async () => {
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
  ["checking", "Checking"],
  ["unavailable", "Unavailable"],
] as const)("announces the %s state", (state, label) => {
  render(<StatusCard state={state} />);
  expect(screen.getByRole("status").textContent).toContain(label);
});
