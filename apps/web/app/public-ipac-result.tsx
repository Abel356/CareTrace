import type { getPublicCitation } from "../lib/public-ipac";

type CitationResult = Awaited<ReturnType<typeof getPublicCitation>>;

export function PublicIpacResult({ result }: { result: CitationResult }) {
  if (result.status === "unavailable") {
    return <p role="status">Citation lookup is unavailable. Try again.</p>;
  }
  if (result.status === "insufficient_evidence") {
    return (
      <p role="status">
        Insufficient evidence for this query and as-of date in the curated IPAC
        snapshot.
      </p>
    );
  }

  const { document, passages, version } = result;
  return (
    <section aria-labelledby="ipac-result-heading" className="citation-result">
      <h3 id="ipac-result-heading">{document.title}</h3>
      <p>
        Ontario ({document.jurisdiction}) · {version.version} · Effective from{" "}
        {version.effective_from} until {version.effective_until} (exclusive)
      </p>
      {passages.map(({ citation_url, locator, span }) => (
        <figure key={JSON.stringify([citation_url, span.start, span.end])}>
          <blockquote cite={citation_url}>{span.quote}</blockquote>
          <figcaption>
            <a href={citation_url}>Ontario e-Laws, {locator}</a>
          </figcaption>
        </figure>
      ))}
    </section>
  );
}
