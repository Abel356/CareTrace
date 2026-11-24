import type { paths } from "@caretrace/contracts/api";
import { fetchApi } from "./api";

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
    const response = await fetchApi("/readyz");
    return response.ok && isReady(await response.json())
      ? "ready"
      : "unavailable";
  } catch {
    return "unavailable";
  }
}
