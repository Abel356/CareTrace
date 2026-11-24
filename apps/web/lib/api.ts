import type { paths } from "@caretrace/contracts/api";

export function fetchApi(path: keyof paths, query?: URLSearchParams) {
  const origin = new URL(
    process.env.CARETRACE_API_ORIGIN ?? "http://127.0.0.1:8000",
  );
  if (
    !["http:", "https:"].includes(origin.protocol) ||
    origin.username ||
    origin.password
  ) {
    throw new Error("Invalid CareTrace API origin");
  }
  const url = new URL(path, origin);
  if (query) url.search = query.toString();
  return fetch(url, {
    cache: "no-store",
    redirect: "error",
    signal: AbortSignal.timeout(2000),
  });
}
