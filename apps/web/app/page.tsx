import { Suspense } from "react";
import { ServiceStatus, StatusCard } from "./service-status";

export default function Home() {
  return (
    <>
      <a className="skip" href="#main">
        Skip to content
      </a>
      <header className="site-header">
        <div className="header-inner">
          <a className="brand" href="#main">
            <span className="brand-mark" aria-hidden="true" />
            CareTrace
          </a>
          <nav aria-label="Workspace">
            <a href="#status">Status</a>
            <a href="#review">Review guidance</a>
          </nav>
        </div>
      </header>
      <main id="main" tabIndex={-1} className="page">
        <div className="intro">
          <div>
            <span className="scope">Ontario long-term care</span>
            <h1>IPAC inspection readiness</h1>
            <p>
              Prepare to review infection prevention and control policies and
              the evidence that supports them.
            </p>
          </div>
          <span className="stage">Discovery prototype</span>
        </div>
        <section id="status" aria-labelledby="status-heading">
          <h2 id="status-heading">Workspace status</h2>
          <div className="cards">
            <Suspense fallback={<StatusCard state="checking" />}>
              <ServiceStatus />
            </Suspense>
            <div className="card">
              <div className="card-header">
                <h3>Source coverage</h3>
                <span className="status status-evidence">
                  Insufficient evidence
                </span>
              </div>
              <p>
                The prototype has no verified regulatory corpus. A source review
                date will appear once sources are checked.
              </p>
            </div>
          </div>
        </section>
        <section
          id="review"
          aria-labelledby="review-heading"
          className="review"
        >
          <h2 id="review-heading">Review guidance</h2>
          <dl>
            <div>
              <dt>Review and approval</dt>
              <dd>
                Treat suggested obligations and coverage as provisional. Have a
                qualified person verify exact citations, applicability dates,
                and evidence before approval. Seek qualified legal advice for
                compliance determinations.
              </dd>
            </div>
            <div>
              <dt>Data handling</dt>
              <dd>
                Use public sources, synthetic examples, or explicitly authorized
                de-identified policies. Keep resident information and unapproved
                client documents out of the workspace.
              </dd>
            </div>
          </dl>
        </section>
      </main>
    </>
  );
}
