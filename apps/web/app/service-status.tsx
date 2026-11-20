import { getReadiness, type Readiness } from "../lib/readiness";

const statusText = {
  checking: { label: "Checking", description: "Checking the CareTrace API." },
  ready: {
    label: "Available",
    description: "The CareTrace API readiness check passed.",
  },
  unavailable: {
    label: "Unavailable",
    description:
      "CareTrace cannot confirm that the API is ready. Reload to try again.",
  },
} satisfies Record<Readiness, { label: string; description: string }>;

export function StatusCard({ state }: { state: Readiness }) {
  const status = statusText[state];
  return (
    <div className="card status-card" role="status">
      <div className="card-header">
        <h3>CareTrace API</h3>
        <span className={`status status-${state}`}>{status.label}</span>
      </div>
      <p>{status.description}</p>
    </div>
  );
}

export async function ServiceStatus() {
  return <StatusCard state={await getReadiness()} />;
}
