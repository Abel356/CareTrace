import type { paths } from "@caretrace/contracts/api";
import { fetchApi } from "./api";

const endpoint = "/api/v1/public/ipac/citations";
type Lookup = paths[typeof endpoint]["get"];
type LookupQuery = Lookup["parameters"]["query"];
type LookupResponse = Lookup["responses"][200]["content"]["application/json"];

export async function getPublicCitation(
  query: LookupQuery,
): Promise<LookupResponse | { status: "unavailable" }> {
  try {
    const response = await fetchApi(endpoint, new URLSearchParams(query));
    if (!response.ok) return { status: "unavailable" };

    const result = (await response.json()) as LookupResponse;
    if (result?.status === "insufficient_evidence") return result;
    if (
      result?.status === "matched" &&
      result.corpus === "public_ipac" &&
      result.document?.jurisdiction === "CA-ON" &&
      typeof result.document.title === "string" &&
      typeof result.version?.version === "string" &&
      typeof result.version.effective_from === "string" &&
      typeof result.version.effective_until === "string" &&
      Array.isArray(result.passages) &&
      result.passages.length > 0 &&
      result.passages.every((passage) => {
        const url = new URL(passage.citation_url);
        return (
          url.protocol === "https:" &&
          !url.username &&
          !url.password &&
          typeof passage.locator === "string" &&
          typeof passage.span?.quote === "string" &&
          passage.span.quote.length > 0
        );
      })
    ) {
      return result;
    }
  } catch {
    return { status: "unavailable" };
  }
  return { status: "unavailable" };
}
