import type { paths } from "@caretrace/contracts/api";

type ReadyPayload =
  paths["/readyz"]["get"]["responses"][200]["content"]["application/json"];
export type Readiness = "checking" | "ready" | "unavailable";

function isReady(payload: unknown): payload is ReadyPayload {
  return (
    typeof payload === "object" &&
    payload !== null &&
    "status" in payload &&
    payload.status === "ready"
  );
}

export async function getReadiness(): Promise<Exclude<Readiness, "checking">> {
  try {
    const origin = new URL(
      process.env.CARETRACE_API_ORIGIN ?? "http://127.0.0.1:8000",
    );
    if (
      !["http:", "https:"].includes(origin.protocol) ||
      origin.username ||
      origin.password
    ) {
      return "unavailable";
    }
    const endpoint = "/readyz" satisfies keyof paths;
    const response = await fetch(new URL(endpoint, origin), {
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(2000),
    });
    return response.ok && isReady(await response.json())
      ? "ready"
      : "unavailable";
  } catch {
    return "unavailable";
  }
}
