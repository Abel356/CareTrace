import { getPublicCitation } from "../lib/public-ipac";
import { PublicIpacResult } from "./public-ipac-result";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;
const maxQueryLength = 200;

function isDate(value: string): boolean {
  if (!/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(value) || value.startsWith("0000")) {
    return false;
  }
  const date = new Date(value);
  return (
    Number.isFinite(date.getTime()) && date.toISOString().startsWith(value)
  );
}

export async function PublicIpacPanel({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const { q, as_of } = await searchParams;
  const query = typeof q === "string" ? q.trim() : "";
  const date = typeof as_of === "string" && isDate(as_of) ? as_of : "";
  const isSubmitted = q !== undefined || as_of !== undefined;
  const isValid = query.length > 0 && query.length <= maxQueryLength && date;
  const result = isValid
    ? await getPublicCitation({ q: query, as_of: date })
    : null;

  return (
    <section
      id="public-ipac"
      aria-labelledby="public-ipac-heading"
      className="card citation-panel"
    >
      <h2 id="public-ipac-heading">Public IPAC citation lookup</h2>
      <p id="public-ipac-scope">
        Search one curated historical excerpt using public terms only.
      </p>
      <form
        action="/#public-ipac"
        method="get"
        className="citation-form"
        aria-describedby="public-ipac-scope"
      >
        <label>
          Search terms
          <input
            type="search"
            name="q"
            defaultValue={query.slice(0, maxQueryLength)}
            maxLength={maxQueryLength}
            required
          />
        </label>
        <label>
          As-of date
          <input type="date" name="as_of" defaultValue={date} required />
        </label>
        <button type="submit">Find citations</button>
      </form>
      {result ? (
        <PublicIpacResult result={result} />
      ) : isSubmitted ? (
        <p role="status">
          Enter search terms of up to {maxQueryLength} characters and a valid
          as-of date.
        </p>
      ) : null}
    </section>
  );
}
