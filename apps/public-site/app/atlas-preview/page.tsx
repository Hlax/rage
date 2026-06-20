// Read-only Research Atlas preview. Static fixture JSON only; no fetches or API routes.

import Link from 'next/link';

import {
  atlasSnapshot,
  coherenceBadgeColor,
  formatEdgeSummary,
  formatPublicTimestamp,
  humanizeLabel,
  resolveAtlasCoherencePreview,
  resolveSourceHealthPreview,
  tinyAtlasConnectionPreview,
} from '../../lib/atlasPreview';
import { conceptToSlug, findCardById, findConceptBySlug } from '../../lib/publicCards';

export const metadata = {
  title: 'Research Atlas Preview — Research Graph Engine',
  description:
    'Text-first read-only preview of the Research Atlas contract using a committed mock staged-spine snapshot.',
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
const smallGridStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
  gap: '0.75rem',
} as const;
const mutedLabelStyle = {
  margin: 0,
  fontSize: '0.75rem',
  color: '#8b93a3',
} as const;

function renderBadgeList(items: string[]) {
  return items.map((item) => (
    <span
      key={item}
      style={{
        display: 'inline-block',
        margin: '0.35rem 0.35rem 0 0',
        padding: '0.2rem 0.5rem',
        border: '1px solid #364052',
        borderRadius: 999,
        color: '#c8d2e8',
        fontSize: '0.75rem',
      }}
    >
      {humanizeLabel(item)}
    </span>
  ));
}

function MetricTile({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div style={{ ...panelStyle, marginBottom: 0 }}>
      <p style={mutedLabelStyle}>{label}</p>
      <p style={{ margin: '0.35rem 0 0', color: '#e6e8ec', fontWeight: 700 }}>
        {value}
      </p>
    </div>
  );
}

function renderConceptLabelList(labels: string[], separator: string) {
  return labels.map((label, index) => {
    const slug = conceptToSlug(label);
    const hasConceptPage = findConceptBySlug(slug) != null;
    return (
      <span key={`${label}-${index}`}>
        {index > 0 ? separator : null}
        {hasConceptPage ? (
          <Link href={`/concepts/${slug}`} style={{ color: '#9eb4ff' }}>
            {label}
          </Link>
        ) : (
          label
        )}
      </span>
    );
  });
}

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
  const connectionPreview = tinyAtlasConnectionPreview;
  const sourceHealthPreview = resolveSourceHealthPreview();
  const readinessEntries = Object.entries(connectionPreview.readiness);

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
        Research Atlas · staged-spine mock preview
      </p>
      <h1 style={{ fontSize: '1.7rem', lineHeight: 1.25, marginTop: '0.35rem' }}>
        {atlasSnapshot.root.primary_question}
      </h1>
      <p style={bodyStyle}>
        This page renders a committed mock-safe staged-spine Atlas snapshot (fixture-mode
        discover→report pipeline) to evaluate whether the contract feels usable before live
        operator exports or graph visualization. It is read-only, static, and disconnected
        from the private research engine — not a live literature review.
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
        <h2 style={headingStyle}>Tiny Atlas connection preview</h2>
        <div style={panelStyle}>
          <p style={mutedLabelStyle}>Research question header</p>
          <h3 style={{ margin: '0.35rem 0', color: '#e6e8ec' }}>
            {connectionPreview.question.primary_question}
          </h3>
          <p style={{ margin: 0, color: '#aeb4c0', lineHeight: 1.55 }}>
            Purpose: {connectionPreview.question.research_purpose}
          </p>
          <p style={{ margin: '0.65rem 0 0', color: '#f0ce78', lineHeight: 1.45 }}>
            Readiness verdict: {connectionPreview.question.readiness_verdict}
          </p>
          <div style={{ marginTop: '0.4rem' }}>
            {renderBadgeList(connectionPreview.question.asset_affordance_tags)}
          </div>
        </div>
      </section>

      <section style={sectionStyle}>
        <h2 style={headingStyle}>Source health panel</h2>
        <p style={{ ...bodyStyle, marginTop: 0, fontSize: '0.85rem' }}>
          Preview source:{' '}
          {sourceHealthPreview.preview_source === 'run_artifact'
            ? 'Atlas-safe source-health run artifact'
            : 'fixture-backed tiny connection preview'}
        </p>
        <div style={smallGridStyle}>
          {Object.entries(sourceHealthPreview.source_counts_by_status).map(
            ([status, count]) => (
              <MetricTile key={status} label={humanizeLabel(status)} value={count} />
            ),
          )}
        </div>
        <div style={{ ...panelStyle, marginTop: '0.75rem' }}>
          <p style={mutedLabelStyle}>Acquisition / parser status</p>
          <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.2rem', color: '#aeb4c0' }}>
            {sourceHealthPreview.acquisition_parser_status.map((item) => (
              <li key={item.status} style={{ marginBottom: '0.4rem' }}>
                <strong style={{ color: '#e6e8ec' }}>{humanizeLabel(item.status)}</strong>{' '}
                ({item.count}) · {item.note}
              </li>
            ))}
          </ul>
          <p style={{ ...mutedLabelStyle, marginTop: '0.8rem' }}>
            Quality gate outcomes
          </p>
          <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0' }}>
            {sourceHealthPreview.quality_gate_outcomes
              .map((item) => `${humanizeLabel(item.outcome)}: ${item.count}`)
              .join(' · ')}
          </p>
        </div>
        <div style={{ ...panelStyle, borderColor: '#5b4332' }}>
          <p style={{ ...mutedLabelStyle, color: '#d9a66f' }}>
            Blocked / dirty / failed source reasons
          </p>
          <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.2rem', color: '#e0c6ad' }}>
            {sourceHealthPreview.blocked_dirty_failed_reasons.map((item) => (
              <li key={item.reason}>
                {humanizeLabel(item.reason)} ({item.count})
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section style={sectionStyle}>
        <h2 style={headingStyle}>Evidence cluster panel</h2>
        <div style={panelStyle}>
          <p style={mutedLabelStyle}>
            {connectionPreview.cluster.cluster_id} · {humanizeLabel(connectionPreview.cluster.maturity)}
          </p>
          <h3 style={{ margin: '0.35rem 0', color: '#e6e8ec' }}>
            {connectionPreview.cluster.cluster_name}
          </h3>
          <p style={{ margin: 0, color: '#aeb4c0' }}>
            Synthesis readiness: {humanizeLabel(connectionPreview.cluster.synthesis_readiness)}
          </p>
          <div style={{ ...smallGridStyle, marginTop: '0.9rem' }}>
            <MetricTile
              label="Relationship density"
              value={connectionPreview.cluster.relationship_density}
            />
            <MetricTile
              label="Source diversity"
              value={connectionPreview.cluster.source_diversity}
            />
            <MetricTile
              label="Claims / atoms / relationships"
              value={`${connectionPreview.cluster.claims_per_cluster} / ${connectionPreview.cluster.atoms_per_cluster} / ${connectionPreview.cluster.relationships_per_cluster}`}
            />
            <MetricTile
              label="Orphan claims / atoms"
              value={`${connectionPreview.cluster.orphan_claim_count} / ${connectionPreview.cluster.orphan_atom_count}`}
            />
          </div>
          <p
            style={{
              margin: '0.9rem 0 0',
              color: connectionPreview.cluster.low_relationship_density ? '#f0a0a0' : '#d9a66f',
            }}
          >
            Relationship-density warning:{' '}
            {connectionPreview.cluster.low_relationship_density
              ? 'low density is active.'
              : connectionPreview.cluster.warning}
          </p>
        </div>
      </section>

      <section style={sectionStyle}>
        <h2 style={headingStyle}>Evidence atom cards</h2>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {connectionPreview.evidence_atoms.map((atom) => (
            <li key={atom.atom_ref} style={panelStyle}>
              <p style={mutedLabelStyle}>
                {atom.atom_ref} · maturity {humanizeLabel(atom.maturity)} · purpose{' '}
                {humanizeLabel(atom.purpose_match_status)}
              </p>
              <p style={{ margin: '0.45rem 0 0', color: '#e6e8ec', lineHeight: 1.5 }}>
                {atom.canonical_atom_text}
              </p>
              <p style={{ margin: '0.6rem 0 0', color: '#8b93a3', fontSize: '0.82rem' }}>
                Supports {atom.support_count} · contradicts {atom.contradiction_count} ·
                qualifies {atom.qualification_count} · sources {atom.source_count}
              </p>
              <div>{renderBadgeList(atom.asset_tags)}</div>
              <p style={{ margin: '0.6rem 0 0', color: '#aeb4c0', lineHeight: 1.45 }}>
                Why clustered: {atom.why_clustered || 'Not clustered yet.'}
              </p>
              <p style={{ margin: '0.35rem 0 0', color: '#d9a66f', lineHeight: 1.45 }}>
                Why weak/partial: {atom.why_weak}
              </p>
            </li>
          ))}
        </ul>
      </section>

      <section style={sectionStyle}>
        <h2 style={headingStyle}>Relationship view</h2>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {connectionPreview.relationships.map((relationship) => (
            <li key={relationship.relationship_ref} style={panelStyle}>
              <p style={mutedLabelStyle}>
                {humanizeLabel(relationship.type)} ·{' '}
                {renderConceptLabelList(relationship.connected_concepts, ' -> ')}
              </p>
              <p style={{ margin: '0.45rem 0 0', color: '#e6e8ec' }}>
                {relationship.summary}
              </p>
              <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.45 }}>
                {relationship.explanation}
              </p>
            </li>
          ))}
        </ul>
      </section>

      <section style={sectionStyle}>
        <h2 style={headingStyle}>Evidence trace detail panel</h2>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {connectionPreview.trace_details.map((trace) => (
            <li key={trace.trace_ref} style={panelStyle}>
              <p style={mutedLabelStyle}>
                {trace.trace_ref} · source status {humanizeLabel(trace.source_status)}
              </p>
              <p style={{ margin: '0.45rem 0 0', color: '#e6e8ec' }}>
                Claim summary: {trace.claim_summary}
              </p>
              <p style={{ margin: '0.45rem 0 0', color: '#8b93a3', fontSize: '0.82rem' }}>
                Atom {trace.atom_ref} · relationships {trace.relationship_links.join(', ')} ·
                cluster {trace.cluster_link}
              </p>
              <p style={{ margin: '0.35rem 0 0', color: '#8b93a3', fontSize: '0.82rem' }}>
                Concepts: {renderConceptLabelList(trace.concept_links, ', ')}
              </p>
              <p style={{ margin: '0.6rem 0 0', color: '#aeb4c0', lineHeight: 1.45 }}>
                {trace.public_safe_connection_explanation}
              </p>
            </li>
          ))}
        </ul>
      </section>

      <section style={sectionStyle}>
        <h2 style={headingStyle}>Gaps / next move panel</h2>
        <div style={smallGridStyle}>
          {readinessEntries.map(([surface, readiness]) => (
            <div key={surface} style={{ ...panelStyle, marginBottom: 0 }}>
              <p style={mutedLabelStyle}>{humanizeLabel(surface)}</p>
              <p
                style={{
                  margin: '0.35rem 0 0',
                  color: readiness.status === 'NO-GO' ? '#f0a0a0' : '#f0ce78',
                  fontWeight: 700,
                }}
              >
                {readiness.status}
              </p>
              <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.45 }}>
                {readiness.reason}
              </p>
            </div>
          ))}
        </div>
        <div style={{ ...panelStyle, marginTop: '0.75rem' }}>
          <p style={mutedLabelStyle}>Top blockers</p>
          <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.2rem', color: '#aeb4c0' }}>
            {connectionPreview.gaps_next_move.top_blockers.map((blocker) => (
              <li key={blocker} style={{ marginBottom: '0.35rem' }}>
                {blocker}
              </li>
            ))}
          </ul>
          <p style={{ ...mutedLabelStyle, marginTop: '0.9rem' }}>Graph health warnings</p>
          <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.2rem', color: '#d9a66f' }}>
            {connectionPreview.gaps_next_move.graph_health_warnings.map((warning) => (
              <li key={warning} style={{ marginBottom: '0.35rem' }}>
                {warning}
              </li>
            ))}
          </ul>
          <p style={{ margin: '0.9rem 0 0', color: '#e6e8ec' }}>
            Next recommended packet: {connectionPreview.gaps_next_move.next_recommended_packet}
          </p>
          <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.45 }}>
            {connectionPreview.gaps_next_move.recommender_reason}
          </p>
        </div>
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
                    Concepts: {renderConceptLabelList(card.concepts, ', ')}
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
            {atlasSnapshot.nodes.map((node, index) => {
              const slug = conceptToSlug(node.label);
              const hasConceptPage = findConceptBySlug(slug) != null;
              return (
                <span key={node.id}>
                  {index > 0 ? ' · ' : null}
                  {hasConceptPage ? (
                    <Link href={`/concepts/${slug}`} style={{ color: '#9eb4ff' }}>
                      {node.label}
                    </Link>
                  ) : (
                    node.label
                  )}
                </span>
              );
            })}
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
                      Concepts:{' '}
                      {renderConceptLabelList(cluster.member_concepts, ', ')}
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
