// Read-only Research Atlas preview. Static fixture JSON only; no fetches or API routes.

import Link from 'next/link';

import {
  atlasSnapshot,
  coherenceBadgeColor,
  formatEdgeSummary,
  formatPublicTimestamp,
  humanizeLabel,
  resolveAtlasCoherencePreview,
} from '../../lib/atlasPreview';
import { findCardById } from '../../lib/publicCards';

export const metadata = {
  title: 'Research Atlas Preview — Research Graph Engine',
  description:
    'Text-first read-only preview of the Research Atlas contract using committed fixture data.',
};

const sectionStyle = { marginTop: '2.25rem' } as const;
const headingStyle = { fontSize: '1.05rem', marginBottom: '0.75rem' } as const;
const bodyStyle = { color: '#aeb4c0', lineHeight: 1.65 } as const;
const panelStyle = {
  border: '1px solid #2a2f3a',
  borderRadius: 8,
  padding: '1rem 1.25rem',
  marginBottom: '0.75rem',
  background: '#161922',
} as const;

function QueuedFollowUps() {
  const queued = atlasSnapshot.follow_up_questions.filter(
    (item) => item.status === 'queued',
  );
  const parked = atlasSnapshot.follow_up_questions.filter(
    (item) => item.status !== 'queued',
  );

  return (
    <>
      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
        {queued.map((item) => (
          <li key={item.id} style={panelStyle}>
            <p style={{ margin: 0, fontSize: '0.75rem', color: '#8b93a3' }}>
              {humanizeLabel(item.status)} · priority {item.priority_score ?? 0}
            </p>
            <p style={{ margin: '0.35rem 0 0', color: '#e6e8ec' }}>
              {item.question_text}
            </p>
            <p style={{ margin: '0.35rem 0 0', fontSize: '0.8rem', color: '#8b93a3' }}>
              {item.reason}
            </p>
          </li>
        ))}
      </ul>
      {parked.length > 0 ? (
        <details style={{ marginTop: '1rem' }}>
          <summary style={{ color: '#8b93a3', cursor: 'pointer' }}>
            Parked follow-ups ({parked.length})
          </summary>
          <ul style={{ listStyle: 'none', padding: 0, margin: '0.75rem 0 0' }}>
            {parked.map((item) => (
              <li key={item.id} style={{ ...panelStyle, opacity: 0.85 }}>
                <p style={{ margin: 0, fontSize: '0.75rem', color: '#8b93a3' }}>
                  {humanizeLabel(item.status)} · {item.reason}
                </p>
                <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0' }}>
                  {item.question_text}
                </p>
              </li>
            ))}
          </ul>
        </details>
      ) : null}
    </>
  );
}

export default function AtlasPreviewPage() {
  const { population, overall_coherence_verdict, preview_label } =
    resolveAtlasCoherencePreview();
  const primaryRun = atlasSnapshot.runs[0];

  return (
    <main style={{ maxWidth: 820, margin: '0 auto', padding: '3rem 1.5rem' }}>
      <p style={{ margin: 0, fontSize: '0.8rem', color: '#8b93a3' }}>
        <Link href="/" style={{ color: '#9eb4ff' }}>
          Public cards
        </Link>
        {' · atlas preview'}
      </p>

      <p
        style={{
          marginTop: '1rem',
          fontSize: '0.8rem',
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: '#8b93a3',
        }}
      >
        Research Atlas · fixture preview v0
      </p>
      <h1 style={{ fontSize: '1.7rem', lineHeight: 1.25, marginTop: '0.35rem' }}>
        {atlasSnapshot.root.primary_question}
      </h1>
      <p style={bodyStyle}>
        This page renders a committed mock-safe Atlas snapshot to evaluate whether the
        contract feels usable before live operator exports or graph visualization.
        It is read-only, static, and disconnected from the private research engine.
      </p>

      <section style={{ marginTop: '1.5rem' }}>
        <span
          style={{
            display: 'inline-block',
            padding: '0.35rem 0.75rem',
            borderRadius: 999,
            fontSize: '0.8rem',
            fontWeight: 600,
            background: coherenceBadgeColor(overall_coherence_verdict),
            color: '#0f1115',
          }}
        >
          Coherence: {humanizeLabel(overall_coherence_verdict)}
        </span>
        <p style={{ ...bodyStyle, marginTop: '0.75rem', fontSize: '0.9rem' }}>
          {preview_label} · snapshot{' '}
          {atlasSnapshot.snapshot_id} · generated{' '}
          {formatPublicTimestamp(atlasSnapshot.generated_at)}
        </p>
        <p style={{ ...bodyStyle, marginTop: '0.35rem', fontSize: '0.85rem' }}>
          Population — runs {population.runs}, cards {population.cards}, nodes{' '}
          {population.nodes}, edges {population.edges}, reports {population.reports},
          clusters {population.clusters}, follow-ups {population.follow_up_questions}
        </p>
      </section>

      <section style={sectionStyle}>
        <h2 style={headingStyle}>Research run summary</h2>
        {primaryRun ? (
          <div style={panelStyle}>
            <p style={{ margin: 0, fontSize: '0.75rem', color: '#8b93a3' }}>
              {humanizeLabel(primaryRun.mode)} · {humanizeLabel(primaryRun.status)} ·{' '}
              {primaryRun.run_id}
            </p>
            <p style={{ margin: '0.5rem 0 0', color: '#e6e8ec' }}>{primaryRun.topic}</p>
            <p style={{ margin: '0.35rem 0 0', fontSize: '0.85rem', color: '#8b93a3' }}>
              Domain pack: {primaryRun.domain_pack}
            </p>
          </div>
        ) : (
          <p style={bodyStyle}>No research runs in this snapshot.</p>
        )}
      </section>

      <section style={sectionStyle}>
        <h2 style={headingStyle}>Domains</h2>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {atlasSnapshot.domains.map((domain) => (
            <li key={domain.id} style={panelStyle}>
              <strong style={{ color: '#e6e8ec' }}>{domain.label}</strong>
              <span style={{ color: '#8b93a3' }}> · {humanizeLabel(domain.role)}</span>
            </li>
          ))}
        </ul>
      </section>

      <section style={sectionStyle}>
        <h2 style={headingStyle}>Cards ({atlasSnapshot.cards.length})</h2>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {atlasSnapshot.cards.map((card) => {
            const publicCard = findCardById(card.id);
            return (
              <li key={card.id} style={panelStyle}>
                <p style={{ margin: 0, fontSize: '0.75rem', color: '#8b93a3' }}>
                  {humanizeLabel(card.type)} · {humanizeLabel(card.confidence)} confidence
                </p>
                <h3 style={{ margin: '0.35rem 0', fontSize: '1rem', color: '#e6e8ec' }}>
                  {publicCard ? (
                    <Link href={`/cards/${card.id}`} style={{ color: '#e6e8ec' }}>
                      {card.title}
                    </Link>
                  ) : (
                    card.title
                  )}
                </h3>
                <p style={{ margin: 0, color: '#aeb4c0', lineHeight: 1.55 }}>
                  {card.summary}
                </p>
                {card.concepts.length > 0 ? (
                  <p style={{ margin: '0.75rem 0 0', fontSize: '0.8rem', color: '#8b93a3' }}>
                    Concepts: {card.concepts.join(', ')}
                  </p>
                ) : null}
              </li>
            );
          })}
        </ul>
      </section>

      <section style={sectionStyle}>
        <h2 style={headingStyle}>
          Nodes ({atlasSnapshot.nodes.length}) · Edges ({atlasSnapshot.edges.length})
        </h2>
        <p style={{ ...bodyStyle, fontSize: '0.9rem' }}>
          Text summary only — no graph visualization in v0.
        </p>
        <div style={panelStyle}>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#8b93a3' }}>Concept nodes</p>
          <p style={{ margin: '0.5rem 0 0', color: '#aeb4c0', lineHeight: 1.6 }}>
            {atlasSnapshot.nodes.map((node) => node.label).join(' · ')}
          </p>
        </div>
        <ul style={{ listStyle: 'none', padding: 0, margin: '0.75rem 0 0' }}>
          {atlasSnapshot.edges.map((edge) => (
            <li key={edge.id} style={panelStyle}>
              <p style={{ margin: 0, color: '#e6e8ec' }}>{formatEdgeSummary(edge)}</p>
              {edge.confidence != null ? (
                <p style={{ margin: '0.35rem 0 0', fontSize: '0.8rem', color: '#8b93a3' }}>
                  Confidence: {edge.confidence}
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      </section>

      <section style={sectionStyle}>
        <h2 style={headingStyle}>Reports ({atlasSnapshot.reports.length})</h2>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {atlasSnapshot.reports.map((report, index) => (
            <li key={`${report.report_type}-${index}`} style={panelStyle}>
              <p style={{ margin: 0, color: '#e6e8ec' }}>
                {humanizeLabel(report.report_type)}
              </p>
              <p style={{ margin: '0.35rem 0 0', fontSize: '0.85rem', color: '#8b93a3' }}>
                Run: {report.run_id ?? '—'} · status {humanizeLabel(report.status ?? 'unknown')}
              </p>
              {report.public_summary ? (
                <p style={{ margin: '0.75rem 0 0', color: '#aeb4c0', lineHeight: 1.55 }}>
                  {report.public_summary}
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      </section>

      <section style={sectionStyle}>
        <h2 style={headingStyle}>Follow-up questions</h2>
        <QueuedFollowUps />
      </section>

      <section style={sectionStyle}>
        <h2 style={headingStyle}>Lineage / research trail</h2>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {atlasSnapshot.runs.map((run) => (
            <li key={run.run_id} style={panelStyle}>
              <p style={{ margin: 0, fontSize: '0.75rem', color: '#8b93a3' }}>
                {run.run_id}
              </p>
              <p style={{ margin: '0.35rem 0 0', color: '#e6e8ec' }}>
                Question id: {run.research_question_id ?? '—'}
              </p>
              <p style={{ margin: '0.25rem 0 0', fontSize: '0.85rem', color: '#8b93a3' }}>
                Parent question: {run.parent_question_id ?? 'none (root)'}
              </p>
            </li>
          ))}
        </ul>
        {atlasSnapshot.clusters.length > 0 ? (
          <div style={{ ...panelStyle, marginTop: '0.75rem' }}>
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#8b93a3' }}>Clusters</p>
            <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.2rem', color: '#aeb4c0' }}>
              {atlasSnapshot.clusters.map((cluster) => (
                <li key={cluster.cluster_id} style={{ marginBottom: '0.5rem' }}>
                  <span>{cluster.cluster_label}</span>
                  {cluster.member_concepts && cluster.member_concepts.length > 0 ? (
                    <p style={{ margin: '0.25rem 0 0', fontSize: '0.85rem', color: '#8b93a3' }}>
                      Concepts: {cluster.member_concepts.join(', ')}
                    </p>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </section>

      <footer
        style={{
          marginTop: '3rem',
          paddingTop: '1rem',
          borderTop: '1px solid #2a2f3a',
          fontSize: '0.8rem',
          color: '#8b93a3',
        }}
      >
        <p style={{ margin: 0 }}>
          Atlas schema {atlasSnapshot.schema_version} · safety audit{' '}
          {atlasSnapshot.safety.safety_audit_id}
        </p>
        <p style={{ margin: '0.25rem 0 0' }}>
          <Link href="/" style={{ color: '#9eb4ff' }}>
            Back to public cards
          </Link>
          {' · '}
          <Link href="/about" style={{ color: '#9eb4ff' }}>
            About
          </Link>
        </p>
      </footer>
    </main>
  );
}
