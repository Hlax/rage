// Read-only Research Atlas preview. Static fixture JSON only; no fetches or API routes.

import Link from 'next/link';

import {
  atlasSnapshot,
  coherenceBadgeColor,
  formatEdgeSummary,
  formatPublicTimestamp,
  humanizeLabel,
  tier2PatchFreshnessBadgeColor,
  tier2PatchFreshnessBadgeLabel,
  tier2PatchValidationVerdictBadgeColor,
  tier2PatchValidationVerdictBadgeLabel,
  resolveAtlasCoherencePreview,
  resolveGapsNextMovePreview,
  resolveGraphMaturityUpgradePreview,
  resolveGraphSummaryPanelPreview,
  resolveLocalModelExtractionComparisonPreview,
  resolveLiveSourceExpansionPreview,
  resolveMultiQuestionLiveAbstractPreview,
  resolvePurposePanelPreview,
  resolveQuestionHeaderPreview,
  resolveReadinessPanelPreview,
  resolveSourceHealthPreview,
  resolveTracePanelPreview,
  resolveWebAdapterScraplingProofPreview,
  resolvePdfTeiMilestonePreview,
  resolveDemoLoopPolishPreview,
  resolveFullAtlasRefreshChecklistPreview,
  resolveOpenAISynthesisAdapterSpecPreview,
  resolveSynthesisHumanReviewPreview,
  resolveSynthesisHumanReviewFlaggedAlerts,
  resolveReleaseGovernorPreview,
  resolveTier2PatchStagingPreview,
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
  const liveSourceExpansionPreview = resolveLiveSourceExpansionPreview();
  const multiQuestionPreview = resolveMultiQuestionLiveAbstractPreview();
  const localModelComparisonPreview = resolveLocalModelExtractionComparisonPreview();
  const graphMaturityPreview = resolveGraphMaturityUpgradePreview();
  const webAdapterPreview = resolveWebAdapterScraplingProofPreview();
  const pdfTeiPreview = resolvePdfTeiMilestonePreview();
  const demoLoopPreview = resolveDemoLoopPolishPreview();
  const fullAtlasRefreshPreview = resolveFullAtlasRefreshChecklistPreview();
  const openaiSynthesisSpecPreview = resolveOpenAISynthesisAdapterSpecPreview();
  const synthesisHumanReviewPreview = resolveSynthesisHumanReviewPreview();
  const synthesisHumanReviewAlerts = resolveSynthesisHumanReviewFlaggedAlerts();
  const releaseGovernorPreview = resolveReleaseGovernorPreview();
  const tier2PatchStagingPreview = resolveTier2PatchStagingPreview();
  const gapsNextMovePreview = resolveGapsNextMovePreview();
  const questionHeaderPreview = resolveQuestionHeaderPreview();
  const readinessPanelPreview = resolveReadinessPanelPreview();
  const purposePanelPreview = resolvePurposePanelPreview();
  const graphSummaryPreview = resolveGraphSummaryPanelPreview();
  const tracePanelPreview = resolveTracePanelPreview();
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
        {questionHeaderPreview.page_subtitle}
      </p>
      {/* Research Atlas · staged-spine mock preview (fixture fallback via atlasPreview.ts) */}
      <h1 style={{ fontSize: '1.7rem', lineHeight: 1.25, marginTop: '0.35rem' }}>
        {questionHeaderPreview.page_title}
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

      {synthesisHumanReviewAlerts ? (
        <section
          id={synthesisHumanReviewAlerts.anchor_id}
          style={{ marginTop: '1.5rem' }}
          aria-live="polite"
        >
          <div
            style={{
              ...panelStyle,
              borderColor: '#7a4a32',
              background: '#221912',
            }}
          >
            <p
              style={{
                margin: 0,
                fontSize: '0.75rem',
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                color: '#f0b07a',
                fontWeight: 700,
              }}
            >
              Operator alert · synthesis human review
            </p>
            <h2
              style={{
                margin: '0.45rem 0 0',
                fontSize: '1.05rem',
                color: '#ffe2cc',
              }}
            >
              {synthesisHumanReviewAlerts.headline}
            </h2>
            <p style={{ margin: '0.55rem 0 0', color: '#e0c6ad', lineHeight: 1.55 }}>
              {synthesisHumanReviewAlerts.summary} Review flagged sentences in the
              operator panel below before promoting synthesis prose.
            </p>
            <ul
              style={{
                margin: '0.85rem 0 0',
                paddingLeft: '1.15rem',
                color: '#f5d5bd',
                lineHeight: 1.5,
              }}
            >
              {synthesisHumanReviewAlerts.alerts.map((alert) => (
                <li key={alert.output_id} style={{ marginBottom: '0.65rem' }}>
                  <strong style={{ color: '#ffe2cc' }}>
                    {alert.output_id}
                  </strong>{' '}
                  · {humanizeLabel(alert.provider)} · packet {alert.packet_id || '—'} ·{' '}
                  {alert.flagged_sentence_count} flagged sentence
                  {alert.flagged_sentence_count === 1 ? '' : 's'}
                  {alert.sentence_preview ? (
                    <>
                      {' '}
                      — &ldquo;{alert.sentence_preview}&rdquo;
                    </>
                  ) : null}
                  <br />
                  <span style={{ color: '#d4a574', fontSize: '0.85rem' }}>
                    {alert.primary_issue}
                  </span>
                </li>
              ))}
            </ul>
            {synthesisHumanReviewAlerts.operator_actions.length > 0 ? (
              <p style={{ margin: '0.75rem 0 0', color: '#c8b4a0', fontSize: '0.85rem' }}>
                Next step: {synthesisHumanReviewAlerts.operator_actions[0]}
              </p>
            ) : null}
          </div>
        </section>
      ) : null}

      <section style={sectionStyle}>
        <h2 style={headingStyle}>Tiny Atlas connection preview</h2>
        <div style={panelStyle}>
          <p style={mutedLabelStyle}>
            Research question header ·{' '}
            {questionHeaderPreview.preview_source === 'run_artifact'
              ? 'Atlas-safe run artifact'
              : 'fixture-backed tiny connection preview'}
          </p>
          <h3 style={{ margin: '0.35rem 0', color: '#e6e8ec' }}>
            {questionHeaderPreview.primary_question}
          </h3>
          <p style={{ margin: 0, color: '#aeb4c0', lineHeight: 1.55 }}>
            Purpose: {questionHeaderPreview.research_purpose}
          </p>
          <p style={{ margin: '0.65rem 0 0', color: '#f0ce78', lineHeight: 1.45 }}>
            Readiness verdict: {questionHeaderPreview.readiness_verdict}
          </p>
          <div style={{ marginTop: '0.4rem' }}>
            {renderBadgeList(questionHeaderPreview.asset_affordance_tags)}
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
          <p style={mutedLabelStyle}>Resolver breakdown</p>
          <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.2rem', color: '#aeb4c0' }}>
            {sourceHealthPreview.resolver_breakdown.map((item) => (
              <li key={item.backend} style={{ marginBottom: '0.4rem' }}>
                <strong style={{ color: '#e6e8ec' }}>{humanizeLabel(item.backend)}</strong>{' '}
                ({item.count}) · {item.note}
              </li>
            ))}
          </ul>
          <p style={{ ...mutedLabelStyle, marginTop: '0.8rem' }}>
            Acquisition / parser status
          </p>
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

      {liveSourceExpansionPreview ? (
        <section style={sectionStyle}>
          <h2 style={headingStyle}>Live source expansion</h2>
          <p style={{ ...bodyStyle, marginTop: 0, fontSize: '0.85rem' }}>
            OpenAlex + arXiv discovery with Unpaywall DOI/OA enrichment. Abstract-first;
            blocked/unavailable sources remain visible in Atlas-safe summaries.
          </p>
          <div style={smallGridStyle}>
            <MetricTile
              label="Expansion verdict"
              value={humanizeLabel(liveSourceExpansionPreview.verdict)}
            />
            <MetricTile
              label="Source diversity"
              value={liveSourceExpansionPreview.source_diversity_count}
            />
            <MetricTile
              label="Resolved records"
              value={liveSourceExpansionPreview.resolved_count}
            />
            <MetricTile
              label="DOI-backed"
              value={liveSourceExpansionPreview.doi_backed_count}
            />
            <MetricTile
              label="Unpaywall enriched"
              value={liveSourceExpansionPreview.unpaywall_enriched_count}
            />
            <MetricTile
              label="Unpaywall enabled"
              value={liveSourceExpansionPreview.enrich_unpaywall ? 'Yes' : 'No'}
            />
          </div>
          <div style={{ ...panelStyle, marginTop: '0.75rem' }}>
            <p style={mutedLabelStyle}>Discovery breakdown (pre-persist)</p>
            <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.2rem', color: '#aeb4c0' }}>
              {liveSourceExpansionPreview.discovery_breakdown.map((item) => (
                <li key={item.backend}>
                  {humanizeLabel(item.backend)} ({item.count})
                </li>
              ))}
            </ul>
            <p style={{ ...mutedLabelStyle, marginTop: '0.8rem' }}>
              Persisted resolver sources
            </p>
            <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.2rem', color: '#aeb4c0' }}>
              {liveSourceExpansionPreview.persisted_breakdown.map((item) => (
                <li key={item.backend}>
                  {humanizeLabel(item.backend)} ({item.count})
                </li>
              ))}
            </ul>
            {liveSourceExpansionPreview.unpaywall_skipped.length ? (
              <>
                <p style={{ ...mutedLabelStyle, marginTop: '0.8rem' }}>
                  Unpaywall skip reasons
                </p>
                <ul
                  style={{ margin: '0.5rem 0 0', paddingLeft: '1.2rem', color: '#aeb4c0' }}
                >
                  {liveSourceExpansionPreview.unpaywall_skipped.map((item) => (
                    <li key={item.reason}>
                      {humanizeLabel(item.reason)} ({item.count})
                    </li>
                  ))}
                </ul>
              </>
            ) : null}
            <p style={{ ...mutedLabelStyle, marginTop: '0.8rem' }}>Rationale</p>
            <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
              {liveSourceExpansionPreview.rationale}
            </p>
          </div>
        </section>
      ) : null}

      {multiQuestionPreview ? (
        <section style={sectionStyle}>
          <h2 style={headingStyle}>Multi-question live abstract runs</h2>
          <p style={{ ...bodyStyle, marginTop: 0, fontSize: '0.85rem' }}>
            Five purpose-gated live abstract evidence runs across open and strict
            creativity questions. Preview source: Atlas-safe multi-question bundle.
          </p>
          <div style={smallGridStyle}>
            <MetricTile
              label="Multi-question verdict"
              value={humanizeLabel(multiQuestionPreview.verdict)}
            />
            <MetricTile
              label="Questions"
              value={multiQuestionPreview.question_count}
            />
            <MetricTile
              label="With live sources"
              value={multiQuestionPreview.questions_with_live_sources}
            />
            <MetricTile
              label="With accepted claims"
              value={multiQuestionPreview.questions_with_accepted_claims}
            />
            <MetricTile
              label="Total accepted claims"
              value={multiQuestionPreview.total_accepted_claims}
            />
            <MetricTile
              label="Purpose routing"
              value={multiQuestionPreview.purpose_routing_valid ? 'Valid' : 'Invalid'}
            />
            <MetricTile
              label="Strict gates"
              value={multiQuestionPreview.strict_gate_count}
            />
            <MetricTile
              label="Open gates"
              value={multiQuestionPreview.open_gate_count}
            />
          </div>
          <div style={{ ...panelStyle, marginTop: '0.75rem' }}>
            <p style={mutedLabelStyle}>Per-question summary</p>
            <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.2rem', color: '#aeb4c0' }}>
              {multiQuestionPreview.per_question_rows.map((row) => (
                <li key={row.question_id} style={{ marginBottom: '0.4rem' }}>
                  <strong style={{ color: '#e6e8ec' }}>{row.question_id}</strong> (
                  {humanizeLabel(row.gate_mode)}) · accepted {row.accepted} / rejected{' '}
                  {row.rejected} · {humanizeLabel(row.verdict)}
                </li>
              ))}
            </ul>
            <p style={{ ...mutedLabelStyle, marginTop: '0.8rem' }}>Rationale</p>
            <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
              {multiQuestionPreview.rationale}
            </p>
          </div>
        </section>
      ) : null}

      {localModelComparisonPreview ? (
        <section style={sectionStyle}>
          <h2 style={headingStyle}>Local model extraction comparison</h2>
          <p style={{ ...bodyStyle, marginTop: 0, fontSize: '0.85rem' }}>
            Evaluation-only: mock deterministic vs local Ollama on the same live
            abstracts. Preview source: Atlas-safe comparison run artifact.
          </p>
          <div style={smallGridStyle}>
            <MetricTile
              label="Comparison verdict"
              value={humanizeLabel(localModelComparisonPreview.comparison_verdict)}
            />
            <MetricTile
              label="Quality vs mock"
              value={humanizeLabel(localModelComparisonPreview.quality_vs_mock_overall)}
            />
            <MetricTile
              label="Abstracts compared"
              value={localModelComparisonPreview.compared_abstract_count}
            />
            <MetricTile
              label="Mock accepted"
              value={localModelComparisonPreview.mock_total_accepted}
            />
            <MetricTile
              label="Ollama accepted"
              value={localModelComparisonPreview.local_ollama_total_accepted}
            />
            <MetricTile
              label="Ollama model"
              value={localModelComparisonPreview.ollama_model}
            />
            <MetricTile
              label="Mock quote validity"
              value={localModelComparisonPreview.mock_quote_validity_rate}
            />
            <MetricTile
              label="Ollama quote validity"
              value={localModelComparisonPreview.local_ollama_quote_validity_rate}
            />
          </div>
          <div style={{ ...panelStyle, marginTop: '0.75rem' }}>
            <p style={mutedLabelStyle}>Per-abstract comparison</p>
            <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.2rem', color: '#aeb4c0' }}>
              {localModelComparisonPreview.per_abstract_rows.map((row) => (
                <li key={row.source_ref} style={{ marginBottom: '0.4rem' }}>
                  <strong style={{ color: '#e6e8ec' }}>{row.source_ref}</strong> (
                  {humanizeLabel(row.resolver_backend)}) · mock {row.mock_accepted} / ollama{' '}
                  {row.ollama_accepted} · {humanizeLabel(row.quality_vs_mock)}
                </li>
              ))}
            </ul>
            {localModelComparisonPreview.ollama_rejection_totals.length > 0 ? (
              <>
                <p style={{ ...mutedLabelStyle, marginTop: '0.8rem' }}>
                  Ollama rejection reasons (aggregate)
                </p>
                <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0' }}>
                  {localModelComparisonPreview.ollama_rejection_totals
                    .map((item) => `${humanizeLabel(item.reason)}: ${item.count}`)
                    .join(' · ')}
                </p>
              </>
            ) : null}
            <p style={{ ...mutedLabelStyle, marginTop: '0.8rem' }}>Rationale</p>
            <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
              {localModelComparisonPreview.comparison_rationale}
            </p>
          </div>
        </section>
      ) : null}

      {graphMaturityPreview ? (
        <section style={sectionStyle}>
          <h2 style={headingStyle}>Graph maturity / evidence atom upgrade</h2>
          <p style={{ ...bodyStyle, marginTop: 0, fontSize: '0.85rem' }}>
            Multi-question live abstract ingest with deterministic concept seeding and
            atom re-clustering. Preview source: Atlas-safe graph maturity artifact.
          </p>
          <div style={smallGridStyle}>
            <MetricTile
              label="Maturity verdict"
              value={humanizeLabel(graphMaturityPreview.verdict)}
            />
            <MetricTile
              label="Questions ingested"
              value={graphMaturityPreview.question_count}
            />
            <MetricTile
              label="Accepted claims"
              value={graphMaturityPreview.total_accepted_claims}
            />
            <MetricTile
              label="Single-claim atoms (before → after)"
              value={`${graphMaturityPreview.before_single_claim_atoms} → ${graphMaturityPreview.after_single_claim_atoms}`}
            />
            <MetricTile
              label="Clustered atoms (before → after)"
              value={`${graphMaturityPreview.before_clustered_atoms} → ${graphMaturityPreview.after_clustered_atoms}`}
            />
            <MetricTile
              label="Relationship density"
              value={`${graphMaturityPreview.relationship_density_before} → ${graphMaturityPreview.relationship_density_after}`}
            />
          </div>
          <div style={{ ...panelStyle, marginTop: '0.75rem' }}>
            <p style={mutedLabelStyle}>Cluster maturity explanations</p>
            <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.2rem', color: '#aeb4c0' }}>
              {graphMaturityPreview.cluster_explanations.map((cluster) => (
                <li key={cluster.cluster_ref} style={{ marginBottom: '0.5rem' }}>
                  <strong style={{ color: '#e6e8ec' }}>{cluster.cluster_ref}</strong> ·{' '}
                  {humanizeLabel(cluster.maturity_label)} · density{' '}
                  {cluster.relationship_density}
                  {cluster.orphan_claim_count > 0
                    ? ` · ${cluster.orphan_claim_count} orphan claim(s)`
                    : ''}
                  <br />
                  <span style={{ fontSize: '0.85rem' }}>{cluster.reasons.join(' ')}</span>
                </li>
              ))}
            </ul>
            <p style={{ ...mutedLabelStyle, marginTop: '0.8rem' }}>Rationale</p>
            <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
              {graphMaturityPreview.rationale}
            </p>
          </div>
        </section>
      ) : null}

      {webAdapterPreview ? (
        <section style={sectionStyle}>
          <h2 style={headingStyle}>Web adapter / Scrapling proof</h2>
          <p style={{ ...bodyStyle, marginTop: 0, fontSize: '0.85rem' }}>
            Public webpage → clean text → quality gate → quote-backed claim → atom/trace.
            Scrapling is acquisition-only; html_to_text is the default CI path.
          </p>
          <div style={smallGridStyle}>
            <MetricTile
              label="Web adapter verdict"
              value={humanizeLabel(webAdapterPreview.verdict)}
            />
            <MetricTile
              label="Parser backend"
              value={humanizeLabel(webAdapterPreview.parser_backend)}
            />
            <MetricTile
              label="Quality gate"
              value={webAdapterPreview.quality_gate_passed ? 'Passed' : 'Failed'}
            />
            <MetricTile
              label="Accepted claims"
              value={webAdapterPreview.accepted_count}
            />
            <MetricTile
              label="Trace rows"
              value={webAdapterPreview.trace_count}
            />
            <MetricTile
              label="Evidence atoms"
              value={webAdapterPreview.evidence_atom_count}
            />
            <MetricTile
              label="Relationships"
              value={webAdapterPreview.relationship_count}
            />
            <MetricTile
              label="Scrapling available"
              value={webAdapterPreview.scrapling_available ? 'Yes' : 'No'}
            />
            <MetricTile
              label="Live fetch"
              value={humanizeLabel(webAdapterPreview.live_fetch_status)}
            />
          </div>
          <div style={{ ...panelStyle, marginTop: '0.75rem' }}>
            <p style={mutedLabelStyle}>Parser comparison (text length)</p>
            <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0' }}>
              html_to_text: {webAdapterPreview.html_to_text_length} chars · scrapling:{' '}
              {webAdapterPreview.scrapling_text_length} chars
            </p>
            <p style={{ ...mutedLabelStyle, marginTop: '0.8rem' }}>Rationale</p>
            <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
              {webAdapterPreview.rationale}
            </p>
          </div>
        </section>
      ) : null}

      {pdfTeiPreview ? (
        <section style={sectionStyle}>
          <h2 style={headingStyle}>PDF / TEI milestone</h2>
          <p style={{ ...bodyStyle, marginTop: 0, fontSize: '0.85rem' }}>
            TEI/XML and PDF parsing with quality gates, dirty-PDF pre-LLM blocking, and
            quote-first full-text extraction through atom/trace reporting.
          </p>
          <div style={smallGridStyle}>
            <MetricTile
              label="PDF / TEI verdict"
              value={humanizeLabel(pdfTeiPreview.verdict)}
            />
            <MetricTile
              label="TEI parser"
              value={humanizeLabel(pdfTeiPreview.tei_parser_backend)}
            />
            <MetricTile
              label="PDF parser"
              value={humanizeLabel(pdfTeiPreview.pdf_parser_backend)}
            />
            <MetricTile
              label="TEI quality gate"
              value={pdfTeiPreview.tei_quality_gate_passed ? 'Passed' : 'Failed'}
            />
            <MetricTile
              label="Dirty PDF blocked"
              value={pdfTeiPreview.dirty_pdf_blocked ? 'Yes' : 'No'}
            />
            <MetricTile
              label="TEI accepted claims"
              value={pdfTeiPreview.tei_accepted_count}
            />
            <MetricTile
              label="TEI trace rows"
              value={pdfTeiPreview.tei_trace_count}
            />
            <MetricTile
              label="PDF accepted claims"
              value={pdfTeiPreview.pdf_accepted_count}
            />
            <MetricTile
              label="TEI quoteable spans"
              value={pdfTeiPreview.tei_quoteable_spans}
            />
          </div>
          <div style={{ ...panelStyle, marginTop: '0.75rem' }}>
            <p style={mutedLabelStyle}>Rationale</p>
            <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
              {pdfTeiPreview.rationale}
            </p>
          </div>
        </section>
      ) : null}

      {demoLoopPreview ? (
        <section style={sectionStyle}>
          <h2 style={headingStyle}>Demo loop polish</h2>
          <p style={{ ...bodyStyle, marginTop: 0, fontSize: '0.85rem' }}>
            One-command fixture research-run: source resolution → abstract evidence → selective
            full-text summary → improvement recommendation → optional DB/trace spine.
          </p>
          <div style={smallGridStyle}>
            <MetricTile
              label="Demo verdict"
              value={humanizeLabel(demoLoopPreview.verdict)}
            />
            <MetricTile
              label="Sources resolved"
              value={demoLoopPreview.resolved_count}
            />
            <MetricTile
              label="Ranked sources"
              value={demoLoopPreview.ranked_source_count}
            />
            <MetricTile
              label="Abstract claims accepted"
              value={demoLoopPreview.accepted_claims_total}
            />
            <MetricTile
              label="Full-text acquisitions"
              value={demoLoopPreview.fulltext_acquisition_count}
            />
            <MetricTile
              label="Full-text clean"
              value={demoLoopPreview.fulltext_clean_count}
            />
            <MetricTile
              label="Trace rows"
              value={demoLoopPreview.trace_count}
            />
            <MetricTile
              label="DB accepted claims"
              value={demoLoopPreview.db_accepted_claims}
            />
            <MetricTile
              label="Recommended packet"
              value={humanizeLabel(demoLoopPreview.recommended_packet)}
            />
          </div>
          <div style={{ ...panelStyle, marginTop: '0.75rem' }}>
            <p style={mutedLabelStyle}>Topic</p>
            <p style={{ margin: '0.35rem 0 0', color: '#e6e8ec', lineHeight: 1.5 }}>
              {demoLoopPreview.topic}
            </p>
            <p style={{ ...mutedLabelStyle, marginTop: '0.8rem' }}>Rationale</p>
            <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
              {demoLoopPreview.rationale}
            </p>
            <p style={{ margin: '0.55rem 0 0', color: '#8b93a3', fontSize: '0.82rem' }}>
              Dominant signal: {humanizeLabel(demoLoopPreview.dominant_signal)}
            </p>
          </div>
        </section>
      ) : null}

      {fullAtlasRefreshPreview ? (
        <section style={sectionStyle}>
          <h2 style={headingStyle}>Full Atlas refresh checklist</h2>
          <p style={{ ...bodyStyle, marginTop: 0, fontSize: '0.85rem' }}>
            Full-cycle operator validation across live source health and all operator-product
            packet artifacts, with optional fixture packet refresh.
          </p>
          <div style={smallGridStyle}>
            <MetricTile
              label="Refresh verdict"
              value={humanizeLabel(fullAtlasRefreshPreview.verdict)}
            />
            <MetricTile
              label="Evidence quality"
              value={humanizeLabel(fullAtlasRefreshPreview.evidence_quality_verdict)}
            />
            <MetricTile
              label="Valid operator packets"
              value={`${fullAtlasRefreshPreview.valid_packet_count} / ${fullAtlasRefreshPreview.total_packet_count}`}
            />
            <MetricTile
              label="Fixture refresh"
              value={humanizeLabel(fullAtlasRefreshPreview.fixture_refresh_status)}
            />
          </div>
          <div style={{ ...panelStyle, marginTop: '0.75rem' }}>
            <p style={mutedLabelStyle}>Rationale</p>
            <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
              {fullAtlasRefreshPreview.rationale}
            </p>
          </div>
        </section>
      ) : null}

      {openaiSynthesisSpecPreview ? (
        <section style={sectionStyle}>
          <h2 style={headingStyle}>OpenAI synthesis adapter spec (ticket-059)</h2>
          <p style={{ ...bodyStyle, marginTop: 0, fontSize: '0.85rem' }}>
            Evidence-packet-only contract and fail-closed env gates. Spec validation only —
            no paid API calls or cloud adapter implementation.
          </p>
          <div style={smallGridStyle}>
            <MetricTile
              label="Spec verdict"
              value={humanizeLabel(openaiSynthesisSpecPreview.verdict)}
            />
            <MetricTile
              label="Ticket-059 status"
              value={humanizeLabel(openaiSynthesisSpecPreview.ticket_status)}
            />
            <MetricTile
              label="Implementation"
              value={
                openaiSynthesisSpecPreview.implementation_blocked ? 'Blocked' : 'Allowed'
              }
            />
            <MetricTile
              label="Example packet"
              value={openaiSynthesisSpecPreview.example_packet_valid ? 'Valid' : 'Invalid'}
            />
          </div>
          <div style={{ ...panelStyle, marginTop: '0.75rem' }}>
            <p style={mutedLabelStyle}>Rationale</p>
            <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
              {openaiSynthesisSpecPreview.rationale}
            </p>
          </div>
        </section>
      ) : null}

      {synthesisHumanReviewPreview ? (
        <section style={sectionStyle} id="synthesis-human-review-panel">
          <h2 style={headingStyle}>Synthesis human review (operator panel)</h2>
          <p style={{ ...bodyStyle, marginTop: 0, fontSize: '0.85rem' }}>
            Atlas-safe queue for cloud synthesis outputs after deterministic grounding,
            budget, safety, and circuit-breaker checks. Read-only preview — no
            approve/write routes.
          </p>
          <div style={smallGridStyle}>
            <MetricTile
              label="Outputs scanned"
              value={synthesisHumanReviewPreview.total_outputs}
            />
            <MetricTile
              label="Needs human review"
              value={synthesisHumanReviewPreview.needs_human_review_count}
            />
            <MetricTile
              label="Grounding passed"
              value={synthesisHumanReviewPreview.grounding_passed_count}
            />
            <MetricTile
              label="Flagged queue"
              value={synthesisHumanReviewPreview.flagged_items.length}
            />
            <MetricTile
              label="Pending sign-off"
              value={synthesisHumanReviewPreview.sign_off_summary.pending_sign_off_count}
            />
            <MetricTile
              label="Signed off"
              value={synthesisHumanReviewPreview.sign_off_summary.signed_off_count}
            />
            <MetricTile
              label="Governor verdict"
              value={humanizeLabel(
                synthesisHumanReviewPreview.governor_summary.automated_review_verdict,
              )}
            />
            <MetricTile
              label="Auto-signed-off"
              value={synthesisHumanReviewPreview.governor_summary.auto_signed_off_count}
            />
            <MetricTile
              label="Governor flagged"
              value={synthesisHumanReviewPreview.governor_summary.flagged_count}
            />
            <MetricTile
              label="Circuit breaker"
              value={humanizeLabel(
                synthesisHumanReviewPreview.governor_summary.circuit_breaker_status,
              )}
            />
          </div>
          <div style={{ ...panelStyle, marginTop: '0.75rem' }}>
            <p style={mutedLabelStyle}>Automated synthesis governor</p>
            <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
              Latest stop reason:{' '}
              {synthesisHumanReviewPreview.governor_summary.latest_stop_reason || 'none'}
            </p>
            <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
              Latest instruction packet:{' '}
              {synthesisHumanReviewPreview.governor_summary.latest_generated_instruction_packet ||
                'not generated'}
            </p>
            <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
              Latest draft ticket:{' '}
              {synthesisHumanReviewPreview.governor_summary.latest_draft_ticket_path ||
                'not created'}{' '}
              ({synthesisHumanReviewPreview.governor_summary.draft_ticket_status || 'missing'})
            </p>
            {synthesisHumanReviewPreview.governor_summary.last_patch_revalidation ? (
              <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
                Post-backfill patch revalidation:{' '}
                {humanizeLabel(
                  synthesisHumanReviewPreview.governor_summary.last_patch_revalidation
                    .validation_verdict ||
                    synthesisHumanReviewPreview.governor_summary.last_patch_revalidation.status ||
                    'unknown',
                )}
                {synthesisHumanReviewPreview.governor_summary.expected_files_backfilled_at
                  ? ` · backfilled ${formatPublicTimestamp(
                      synthesisHumanReviewPreview.governor_summary.expected_files_backfilled_at,
                    )}`
                  : ''}
              </p>
            ) : null}
            <p style={{ margin: '0.35rem 0 0', color: '#8b93a3', fontSize: '0.82rem' }}>
              Handoff:{' '}
              {synthesisHumanReviewPreview.governor_summary
                .local_implementation_handoff_recommended
                ? 'local implementation draft ready'
                : synthesisHumanReviewPreview.governor_summary
                      .instruction_packet_ticket_draft_recommended
                  ? 'create draft ticket from instruction packet'
                  : 'not recommended'}
            </p>
            <p style={{ margin: '0.35rem 0 0', color: '#8b93a3', fontSize: '0.82rem' }}>
              Providers:{' '}
              {Object.entries(synthesisHumanReviewPreview.governor_summary.provider_summary)
                .map(([provider, count]) => `${humanizeLabel(provider)} (${count})`)
                .join(' · ') || 'none'}
            </p>
            <p style={{ margin: '0.35rem 0 0', color: '#8b93a3', fontSize: '0.82rem' }}>
              Cost cap:{' '}
              {synthesisHumanReviewPreview.governor_summary.cost_summary.max_usd_per_run ??
                'n/a'}{' '}
              USD · token cap{' '}
              {synthesisHumanReviewPreview.governor_summary.cost_summary.max_tokens_per_call ??
                'n/a'}{' '}
              · paid calls{' '}
              {synthesisHumanReviewPreview.governor_summary.cost_summary.no_paid_api_calls ===
              false
                ? 'yes'
                : 'no/unknown'}
            </p>
          </div>
          <div style={{ ...panelStyle, marginTop: '0.75rem' }}>
            <p style={mutedLabelStyle}>Circuit breaker operator guidance</p>
            <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
              Status:{' '}
              {humanizeLabel(
                synthesisHumanReviewPreview.circuit_breaker_guidance.circuit_breaker_status,
              )}
            </p>
            <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
              Reason opened:{' '}
              {synthesisHumanReviewPreview.circuit_breaker_guidance.reason_opened || 'none'}
            </p>
            <p style={{ margin: '0.35rem 0 0', color: '#8b93a3', fontSize: '0.82rem' }}>
              Failures: synthesis{' '}
              {synthesisHumanReviewPreview.circuit_breaker_guidance.consecutive_synthesis_failures}{' '}
              · unsupported{' '}
              {
                synthesisHumanReviewPreview.circuit_breaker_guidance
                  .consecutive_unsupported_outputs
              }
            </p>
            <p style={{ margin: '0.35rem 0 0', color: '#8b93a3', fontSize: '0.82rem' }}>
              Ledger:{' '}
              {synthesisHumanReviewPreview.circuit_breaker_guidance.latest_ledger_path || 'none'}
            </p>
            <p style={{ margin: '0.35rem 0 0', color: '#8b93a3', fontSize: '0.82rem' }}>
              Reset: {synthesisHumanReviewPreview.circuit_breaker_guidance.reset_instructions}
            </p>
          </div>
          {synthesisHumanReviewPreview.flagged_items.length > 0 ? (
            synthesisHumanReviewPreview.flagged_items.map((item) => (
              <div key={item.output_id} style={{ ...panelStyle, marginTop: '0.75rem' }}>
                <p style={mutedLabelStyle}>
                  {item.output_id} · {humanizeLabel(item.provider)} ·{' '}
                  {humanizeLabel(item.review_status)}
                </p>
                <p style={{ margin: '0.35rem 0 0', color: '#8b93a3', fontSize: '0.82rem' }}>
                  Packet {item.packet_id || '—'} · {item.flagged_sentence_count} flagged /{' '}
                  {item.sentence_count} sentences
                </p>
                {item.flagged_sentences.map((sentence) => (
                  <div
                    key={`${item.output_id}-${sentence.index}`}
                    style={{
                      marginTop: '0.65rem',
                      paddingTop: '0.65rem',
                      borderTop: '1px solid #2a2f3a',
                    }}
                  >
                    <p style={{ margin: 0, color: '#e6e8ec', lineHeight: 1.5 }}>
                      {sentence.text}
                    </p>
                    <p style={{ margin: '0.45rem 0 0', color: '#8b93a3', fontSize: '0.82rem' }}>
                      Claims: {sentence.cited_claim_refs.join(', ') || '—'} · Atoms:{' '}
                      {sentence.cited_atom_refs.join(', ') || '—'} · Overlap:{' '}
                      {sentence.min_overlap_count}
                    </p>
                    {sentence.issues.length > 0 ? (
                      <ul
                        style={{
                          margin: '0.45rem 0 0',
                          paddingLeft: '1.1rem',
                          color: '#d4a574',
                          fontSize: '0.82rem',
                          lineHeight: 1.45,
                        }}
                      >
                        {sentence.issues.map((issue) => (
                          <li key={issue}>{issue}</li>
                        ))}
                      </ul>
                    ) : null}
                  </div>
                ))}
              </div>
            ))
          ) : (
            <div style={{ ...panelStyle, marginTop: '0.75rem' }}>
              <p style={{ margin: 0, color: '#aeb4c0', lineHeight: 1.5 }}>
                No synthesis outputs currently flagged for human review.
              </p>
            </div>
          )}
          {synthesisHumanReviewPreview.pending_sign_offs.length > 0 ? (
            <div style={{ ...panelStyle, marginTop: '0.75rem' }} id="synthesis-sign-off-pending">
              <p style={mutedLabelStyle}>Pending operator sign-off</p>
              <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', fontSize: '0.85rem' }}>
                Grounding passed — record CLI sign-off before promoting synthesis prose.
              </p>
              {synthesisHumanReviewPreview.pending_sign_offs.map((item) => (
                <div
                  key={item.output_id}
                  style={{
                    marginTop: '0.65rem',
                    paddingTop: '0.65rem',
                    borderTop: '1px solid #2a2f3a',
                  }}
                >
                  <p style={{ margin: 0, color: '#e6e8ec', lineHeight: 1.5 }}>
                    {item.output_id} · {humanizeLabel(item.provider)} ·{' '}
                    {item.sentence_count} sentence(s)
                  </p>
                  <p style={{ margin: '0.35rem 0 0', color: '#8b93a3', fontSize: '0.82rem' }}>
                    Packet {item.packet_id || '—'} · status {humanizeLabel(item.sign_off_status || 'pending')}
                  </p>
                </div>
              ))}
            </div>
          ) : null}
          {synthesisHumanReviewPreview.signed_off_outputs.length > 0 ? (
            <div style={{ ...panelStyle, marginTop: '0.75rem' }} id="synthesis-sign-off-completed">
              <p style={mutedLabelStyle}>Signed off</p>
              {synthesisHumanReviewPreview.signed_off_outputs.map((item) => (
                <div
                  key={item.output_id}
                  style={{
                    marginTop: '0.65rem',
                    paddingTop: '0.65rem',
                    borderTop: '1px solid #2a2f3a',
                  }}
                >
                  <p style={{ margin: 0, color: '#9fd4a8', lineHeight: 1.5 }}>
                    {item.output_id} · {humanizeLabel(item.provider)}
                  </p>
                  <p style={{ margin: '0.35rem 0 0', color: '#8b93a3', fontSize: '0.82rem' }}>
                    {item.sign_off_id || '—'} · {item.signed_off_at || '—'}
                  </p>
                </div>
              ))}
            </div>
          ) : null}
          {synthesisHumanReviewPreview.operator_actions.length > 0 ? (
            <div style={{ ...panelStyle, marginTop: '0.75rem' }}>
              <p style={mutedLabelStyle}>Operator actions</p>
              <ul
                style={{
                  margin: '0.45rem 0 0',
                  paddingLeft: '1.1rem',
                  color: '#aeb4c0',
                  fontSize: '0.85rem',
                  lineHeight: 1.5,
                }}
              >
                {synthesisHumanReviewPreview.operator_actions.map((action) => (
                  <li key={action}>{action}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>
      ) : null}

      {releaseGovernorPreview ? (
        <section style={sectionStyle} id="release-governor-panel">
          <h2 style={headingStyle}>Release governor (operator panel)</h2>
          <p style={{ ...bodyStyle, marginTop: 0, fontSize: '0.85rem' }}>
            Autonomy tier, release batch status, and gated push/merge/publish recommendations.
            Read-only preview — no auto-merge or publish routes.
          </p>
          <div style={smallGridStyle}>
            <MetricTile
              label="Autonomy tier"
              value={humanizeLabel(releaseGovernorPreview.autonomy_tier.tier_name)}
            />
            <MetricTile
              label="Governor verdict"
              value={humanizeLabel(releaseGovernorPreview.governor_verdict)}
            />
            <MetricTile
              label="Batch status"
              value={humanizeLabel(releaseGovernorPreview.batch_status)}
            />
            <MetricTile
              label="Circuit breaker"
              value={humanizeLabel(releaseGovernorPreview.circuit_breaker_status)}
            />
            <MetricTile
              label="Dry-run recommended"
              value={releaseGovernorPreview.release_governor_dry_run_recommended ? 'yes' : 'no'}
            />
            <MetricTile
              label="Batch assemble recommended"
              value={releaseGovernorPreview.batch_candidate_recommended ? 'yes' : 'no'}
            />
            <MetricTile
              label="Next release action"
              value={humanizeLabel(releaseGovernorPreview.next_release_action || 'none')}
            />
          </div>
          <div style={{ ...panelStyle, marginTop: '0.75rem' }}>
            <p style={mutedLabelStyle}>Release batch</p>
            <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
              Latest batch: {releaseGovernorPreview.latest_batch_path || 'none'}{' '}
              {releaseGovernorPreview.latest_batch_id
                ? `(${releaseGovernorPreview.latest_batch_id})`
                : ''}
            </p>
            <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
              Latest draft ticket: {releaseGovernorPreview.latest_draft_ticket_path || 'none'}
            </p>
            <p style={{ margin: '0.35rem 0 0', color: '#8b93a3', fontSize: '0.82rem' }}>
              Push: {releaseGovernorPreview.release_push_recommended ? 'recommended' : 'blocked'} ·
              Merge: {releaseGovernorPreview.release_merge_recommended ? 'recommended' : 'blocked'} ·
              Publish:{' '}
              {releaseGovernorPreview.release_publish_recommended ? 'recommended' : 'blocked'}
            </p>
            {releaseGovernorPreview.batch_assembly_block_reasons &&
            releaseGovernorPreview.batch_assembly_block_reasons.length > 0 ? (
              <p style={{ margin: '0.35rem 0 0', color: '#c9a227', fontSize: '0.82rem' }}>
                Blocked reasons:{' '}
                {releaseGovernorPreview.batch_assembly_block_reasons.join(' · ')}
              </p>
            ) : null}
            {releaseGovernorPreview.failure_reasons.length > 0 ? (
              <p style={{ margin: '0.35rem 0 0', color: '#c9a227', fontSize: '0.82rem' }}>
                Failure reasons: {releaseGovernorPreview.failure_reasons.join(' · ')}
              </p>
            ) : null}
          </div>
        </section>
      ) : null}

      {tier2PatchStagingPreview ? (
        <section style={sectionStyle} id="tier2-patch-staging-panel">
          <h2 style={headingStyle}>Tier 2 patch staging (operator panel)</h2>
          <div style={{ marginTop: '0.5rem', marginBottom: '0.75rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            <span
              style={{
                display: 'inline-block',
                padding: '0.35rem 0.75rem',
                borderRadius: 999,
                fontSize: '0.8rem',
                fontWeight: 600,
                background: tier2PatchValidationVerdictBadgeColor(
                  tier2PatchStagingPreview.validation_verdict,
                ),
                color: '#0f1115',
              }}
            >
              {tier2PatchValidationVerdictBadgeLabel(
                tier2PatchStagingPreview.validation_verdict,
              )}
            </span>
            <span
              style={{
                display: 'inline-block',
                padding: '0.35rem 0.75rem',
                borderRadius: 999,
                fontSize: '0.8rem',
                fontWeight: 600,
                background: tier2PatchFreshnessBadgeColor(
                  tier2PatchStagingPreview.preview_freshness,
                ),
                color: '#0f1115',
              }}
            >
              {tier2PatchFreshnessBadgeLabel(tier2PatchStagingPreview.preview_freshness)}
            </span>
          </div>
          <p style={{ ...bodyStyle, marginTop: 0, fontSize: '0.85rem' }}>
            Latest staged local implementation patch bundle and diff-quality verdict.
            Read-only summary — no raw diff or file contents.
          </p>
          <div style={smallGridStyle}>
            <MetricTile
              label="Validation verdict"
              value={humanizeLabel(tier2PatchStagingPreview.validation_verdict)}
            />
            <MetricTile
              label="Risk class"
              value={humanizeLabel(tier2PatchStagingPreview.risk_class)}
            />
            <MetricTile
              label="Changed files"
              value={tier2PatchStagingPreview.changed_file_count}
            />
            <MetricTile
              label="Lines added"
              value={tier2PatchStagingPreview.lines_added}
            />
            <MetricTile
              label="Lines removed"
              value={tier2PatchStagingPreview.lines_removed}
            />
            <MetricTile
              label="Safety audit required"
              value={tier2PatchStagingPreview.safety_audit_required ? 'yes' : 'no'}
            />
            <MetricTile
              label="Preview freshness"
              value={humanizeLabel(tier2PatchStagingPreview.preview_freshness)}
            />
            {tier2PatchStagingPreview.patch_revalidation_summary ? (
              <MetricTile
                label="Post-backfill revalidation"
                value={
                  tier2PatchStagingPreview.patch_revalidation_summary.validation_verdict
                    ? humanizeLabel(
                        tier2PatchStagingPreview.patch_revalidation_summary.validation_verdict,
                      )
                    : humanizeLabel(
                        tier2PatchStagingPreview.patch_revalidation_summary.status || 'none',
                      )
                }
              />
            ) : null}
            <MetricTile
              label="Next action"
              value={humanizeLabel(tier2PatchStagingPreview.next_recommended_action)}
            />
          </div>
          <div style={{ ...panelStyle, marginTop: '0.75rem' }}>
            <p style={mutedLabelStyle}>Staged patch summary</p>
            <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
              Draft ticket: {tier2PatchStagingPreview.draft_ticket_label || 'none'}
              {tier2PatchStagingPreview.draft_ticket_path_summary
                ? ` (${tier2PatchStagingPreview.draft_ticket_path_summary})`
                : ''}
            </p>
            <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
              Branch: {tier2PatchStagingPreview.branch_name || 'none'}
            </p>
            <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
              Instruction packet: {tier2PatchStagingPreview.instruction_packet_label || 'none'}
            </p>
            <p style={{ margin: '0.35rem 0 0', color: '#8b93a3', fontSize: '0.82rem' }}>
              Apply ready: {tier2PatchStagingPreview.apply_ready ? 'yes' : 'no'} · Stop/fix
              state: {tier2PatchStagingPreview.stop_state ? 'yes' : 'no'} · Test plan items:{' '}
              {tier2PatchStagingPreview.test_plan_count}
            </p>
            {tier2PatchStagingPreview.validation_reasons.length > 0 ? (
              <p style={{ margin: '0.35rem 0 0', color: '#c9a227', fontSize: '0.82rem' }}>
                Validation reasons: {tier2PatchStagingPreview.validation_reasons.join(' · ')}
              </p>
            ) : null}
          </div>
        </section>
      ) : null}

      <section style={sectionStyle}>
        <h2 style={headingStyle}>Purpose panel</h2>
        <p style={{ ...bodyStyle, marginTop: 0, fontSize: '0.85rem' }}>
          Preview source:{' '}
          {purposePanelPreview.preview_source === 'run_artifact'
            ? 'Atlas-safe run artifact purpose metadata'
            : 'fixture-backed question purpose block'}
        </p>
        <div style={panelStyle}>
          <p style={mutedLabelStyle}>Domain pack · {purposePanelPreview.domain_pack}</p>
          <p style={{ margin: '0.45rem 0 0', color: '#e6e8ec', lineHeight: 1.5 }}>
            Research intents: {purposePanelPreview.research_intents.join(' · ') || '—'}
          </p>
          <p style={{ margin: '0.45rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
            Evidence need: {purposePanelPreview.evidence_need}
          </p>
          <p style={{ margin: '0.45rem 0 0', color: '#aeb4c0', lineHeight: 1.5 }}>
            Maturity / training: {purposePanelPreview.evidence_maturity} ·{' '}
            {purposePanelPreview.training_suitability}
          </p>
          <div style={{ marginTop: '0.55rem' }}>
            {renderBadgeList(purposePanelPreview.asset_affordances)}
          </div>
          {purposePanelPreview.acceptable_source_types.length > 0 ? (
            <p style={{ margin: '0.75rem 0 0', color: '#8b93a3', fontSize: '0.82rem' }}>
              Acceptable sources: {purposePanelPreview.acceptable_source_types.join(', ')}
            </p>
          ) : null}
          {purposePanelPreview.output_targets.length > 0 ? (
            <p style={{ margin: '0.35rem 0 0', color: '#8b93a3', fontSize: '0.82rem' }}>
              Output targets: {purposePanelPreview.output_targets.join(', ')}
            </p>
          ) : null}
        </div>
        {Object.keys(purposePanelPreview.purpose_fit_counts).length > 0 ||
        Object.keys(purposePanelPreview.gate_decision_counts).length > 0 ? (
          <div style={{ ...smallGridStyle, marginTop: '0.75rem' }}>
            {Object.entries(purposePanelPreview.purpose_fit_counts).map(([label, count]) => (
              <MetricTile key={`fit-${label}`} label={`Purpose fit · ${label}`} value={count} />
            ))}
            {Object.entries(purposePanelPreview.gate_decision_counts).map(([label, count]) => (
              <MetricTile key={`gate-${label}`} label={`Gate · ${label}`} value={count} />
            ))}
          </div>
        ) : null}
      </section>

      <section style={sectionStyle}>
        <h2 style={headingStyle}>Graph summary panel</h2>
        <p style={{ ...bodyStyle, marginTop: 0, fontSize: '0.85rem' }}>
          Preview source:{' '}
          {graphSummaryPreview.preview_source === 'run_artifact'
            ? 'Atlas-safe run artifact graph summary'
            : 'fixture-backed cluster and relationship preview'}
        </p>
        <div style={smallGridStyle}>
          <MetricTile
            label="Relationship density"
            value={graphSummaryPreview.relationship_density}
          />
          <MetricTile
            label="Relationship count"
            value={graphSummaryPreview.relationship_count}
          />
          <MetricTile
            label="Clustered atoms"
            value={graphSummaryPreview.clustered_atom_count}
          />
          <MetricTile
            label="Weak atoms"
            value={graphSummaryPreview.weak_atom_count}
          />
          <MetricTile
            label="Multi-claim atoms"
            value={graphSummaryPreview.multi_claim_atom_count}
          />
          <MetricTile
            label="Source-diverse atoms"
            value={graphSummaryPreview.source_diverse_atom_count}
          />
          <MetricTile
            label="Orphan claims"
            value={graphSummaryPreview.orphan_claim_count}
          />
          <MetricTile
            label="Orphan atoms"
            value={graphSummaryPreview.orphan_atom_count}
          />
          <MetricTile
            label="Synthesis-ready clusters"
            value={graphSummaryPreview.synthesis_ready_cluster_count}
          />
          <MetricTile
            label="Frontend-ready traces"
            value={graphSummaryPreview.frontend_ready_trace_count}
          />
        </div>
        <div style={{ ...panelStyle, marginTop: '0.75rem' }}>
          <p style={mutedLabelStyle}>Edge type counts</p>
          <p style={{ margin: '0.45rem 0 0', color: '#aeb4c0', lineHeight: 1.55 }}>
            {Object.entries(graphSummaryPreview.edge_type_counts)
              .map(([edgeType, count]) => `${humanizeLabel(edgeType)}: ${count}`)
              .join(' · ') || 'No relationship edges recorded.'}
          </p>
          <p style={{ margin: '0.75rem 0 0', color: '#f0ce78', lineHeight: 1.45 }}>
            Graph readiness verdict: {graphSummaryPreview.graph_readiness_verdict}
          </p>
        </div>
        <div style={{ ...panelStyle, marginTop: '0.75rem', borderColor: '#5b4332' }}>
          <p style={{ ...mutedLabelStyle, color: '#d9a66f' }}>Top graph blockers</p>
          <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.2rem', color: '#e0c6ad' }}>
            {graphSummaryPreview.top_graph_blockers.map((blocker) => (
              <li key={blocker} style={{ marginBottom: '0.35rem' }}>
                {blocker}
              </li>
            ))}
          </ul>
          <p style={{ margin: '0.9rem 0 0', color: '#e6e8ec' }}>
            Next recommended packet: {graphSummaryPreview.next_recommended_packet}
          </p>
          <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.45 }}>
            {graphSummaryPreview.recommender_reason}
          </p>
        </div>
      </section>

      <section style={sectionStyle}>
        <h2 style={headingStyle}>Readiness panel</h2>
        <p style={{ ...bodyStyle, marginTop: 0, fontSize: '0.85rem' }}>
          Preview source:{' '}
          {readinessPanelPreview.preview_source === 'run_artifact'
            ? 'Atlas-safe run artifact readiness warnings'
            : 'fixture-backed readiness surfaces'}
        </p>
        <div style={panelStyle}>
          <p style={mutedLabelStyle}>
            Readiness warnings ({readinessPanelPreview.warning_count})
          </p>
          <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.2rem', color: '#aeb4c0' }}>
            {readinessPanelPreview.warnings.map((warning) => (
              <li
                key={`${warning.label}-${warning.detail}`}
                style={{
                  marginBottom: '0.45rem',
                  color:
                    warning.severity === 'blocker'
                      ? '#f0a0a0'
                      : warning.severity === 'warning'
                        ? '#f0ce78'
                        : '#aeb4c0',
                }}
              >
                <strong style={{ color: '#e6e8ec' }}>{warning.label}</strong>: {warning.detail}
              </li>
            ))}
          </ul>
        </div>
        {readinessPanelPreview.preview_source === 'fixture' ? (
          <div style={{ ...smallGridStyle, marginTop: '0.75rem' }}>
            {Object.entries(readinessPanelPreview.readiness_surfaces).map(
              ([surface, readiness]) => (
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
              ),
            )}
          </div>
        ) : null}
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
        <p style={{ ...bodyStyle, marginTop: 0, fontSize: '0.85rem' }}>
          Preview source:{' '}
          {tracePanelPreview.preview_source === 'run_artifact'
            ? 'Atlas-safe source-health run artifact'
            : 'fixture-backed tiny connection preview'}
          {' · '}
          {tracePanelPreview.trace_count} trace(s) · {tracePanelPreview.atom_count} atom(s) ·{' '}
          {tracePanelPreview.accepted_claim_count} accepted claim(s)
        </p>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {tracePanelPreview.trace_details.map((trace) => (
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
        <p style={{ ...bodyStyle, marginTop: 0, fontSize: '0.85rem' }}>
          Preview source:{' '}
          {gapsNextMovePreview.preview_source === 'run_artifact'
            ? 'Atlas-safe source-health run artifact'
            : 'fixture-backed tiny connection preview'}
        </p>
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
            {gapsNextMovePreview.top_blockers.map((blocker) => (
              <li key={blocker} style={{ marginBottom: '0.35rem' }}>
                {blocker}
              </li>
            ))}
          </ul>
          <p style={{ ...mutedLabelStyle, marginTop: '0.9rem' }}>Graph health warnings</p>
          <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.2rem', color: '#d9a66f' }}>
            {gapsNextMovePreview.graph_health_warnings.map((warning) => (
              <li key={warning} style={{ marginBottom: '0.35rem' }}>
                {warning}
              </li>
            ))}
          </ul>
          <p style={{ margin: '0.9rem 0 0', color: '#e6e8ec' }}>
            Next recommended packet: {gapsNextMovePreview.next_recommended_packet}
          </p>
          <p style={{ margin: '0.35rem 0 0', color: '#aeb4c0', lineHeight: 1.45 }}>
            {gapsNextMovePreview.recommender_reason}
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
