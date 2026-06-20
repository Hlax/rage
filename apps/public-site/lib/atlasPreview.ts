import snapshot from '../public/data/atlas_snapshot_preview.json';
import coherence from '../public/data/atlas_coherence_preview.json';
import connectionPreview from '../public/data/tiny_atlas_connection_preview.json';
import sourceHealthRun from '../public/data/atlas_source_health_run_latest.json';

import { formatPublicTimestamp, humanizeLabel } from './publicCards';

export type AtlasPreviewCard = {
  id: string;
  type: string;
  title: string;
  summary: string;
  confidence: string;
  concepts: string[];
  source_count?: number;
  public_caveats?: string[];
};

export type AtlasPreviewRun = {
  run_id: string;
  topic: string;
  domain_pack: string;
  mode: string;
  status: string;
  research_question_id?: string;
  parent_question_id?: string | null;
};

export type AtlasPreviewNode = {
  id: string;
  node_type: string;
  label: string;
  domain_pack?: string;
};

export type AtlasPreviewEdge = {
  id: string;
  edge_type: string;
  predicate: string;
  source_label: string;
  target_label: string;
  scope?: string;
  confidence?: number;
};

export type AtlasPreviewFollowUp = {
  id: string;
  research_question_id?: string;
  reason: string;
  status: string;
  question_text: string;
  priority_score?: number;
};

export type AtlasCoherenceSummary = {
  overall_coherence_verdict: string;
  preview_label: string;
};

export type AtlasPreviewSnapshot = {
  schema_version: string;
  generated_at: string;
  snapshot_id: string;
  root: {
    topic: string;
    primary_question: string;
    domain_pack: string;
  };
  domains: Array<{ id: string; label: string; role: string }>;
  runs: AtlasPreviewRun[];
  nodes: AtlasPreviewNode[];
  edges: AtlasPreviewEdge[];
  clusters: Array<{
    cluster_id: string;
    cluster_label: string;
    run_id?: string | null;
    member_concepts?: string[];
  }>;
  reports: Array<{
    report_type: string;
    schema_version?: string;
    run_id?: string;
    status?: string;
    public_summary?: string;
  }>;
  cards: AtlasPreviewCard[];
  follow_up_questions: AtlasPreviewFollowUp[];
  safety: { public_safe: boolean; safety_audit_id: string };
  coherence_summary?: AtlasCoherenceSummary;
};

export type AtlasCoherencePreview = {
  schema_version: string;
  overall_coherence_verdict: string;
  population: Record<string, number>;
  preview_label: string;
};

export type AtlasSourceHealthPanel = {
  source_counts_by_status: Record<string, number>;
  acquisition_parser_status: Array<{ status: string; count: number; note: string }>;
  quality_gate_outcomes: Array<{ outcome: string; count: number }>;
  blocked_dirty_failed_reasons: Array<{ reason: string; count: number }>;
};

export type AtlasSourceHealthRunArtifact = {
  schema_version: string;
  status: string;
  question: string;
  domain_pack: string;
  source_health_summary: {
    source_status_counts: Record<string, number>;
    acquisition_status_counts: Record<string, number>;
    parser_backend_counts: Record<string, number>;
    quality_gate_status_counts: Record<string, number>;
    failure_reason_counts: Record<string, number>;
    purpose_fit_status_counts?: Record<string, number>;
    sources_with_metadata: number;
  };
  readiness_warnings?: string[];
  next_recommended_packet?: string;
  next_recommended_reason?: string;
  purpose_fit_summary?: {
    source_counts?: Record<string, number>;
    gate_decision_counts?: Record<string, number>;
    accepted_evidence_count?: number;
    rejected_evidence_count?: number;
  };
  graph_summary?: {
    claims?: number;
    atoms?: number;
    relationships?: number;
    connection_metrics?: {
      clusters?: Array<{
        cluster_id?: string;
        relationship_density?: number;
        low_relationship_density?: boolean;
      }>;
      totals?: Record<string, number>;
    };
  };
  purpose?: {
    research_intent?: string[];
    asset_affordance?: string[];
    evidence_maturity?: string;
    training_suitability?: string;
    evidence_need?: string;
    acceptable_source_types?: string[];
    output_targets?: string[];
  };
  trace_summary?: {
    trace_count?: number;
    frontend_ready_trace_count?: number;
    atom_count?: number;
    accepted_claim_count?: number;
    atlas_trace_preview?: Array<{
      trace_ref?: string;
      connection_type?: string;
      maturity?: string;
      atom_cluster_maturity?: string;
      purpose_match_status?: string;
      evidence_decision?: string;
      visibility?: string;
      has_quote?: boolean;
      concept_count?: number;
      relationship_count?: number;
      relationship_types?: string[];
      relationship_type?: string;
      why_clustered?: string;
      why_evidence_downgraded_or_rejected?: string;
      why_connected?: string;
    }>;
  };
};

export type AtlasPurposePanelPreview = {
  domain_pack: string;
  research_intents: string[];
  asset_affordances: string[];
  evidence_maturity: string;
  training_suitability: string;
  evidence_need: string;
  acceptable_source_types: string[];
  output_targets: string[];
  purpose_fit_counts: Record<string, number>;
  gate_decision_counts: Record<string, number>;
};

export type AtlasQuestionHeaderPreview = {
  topic: string;
  primary_question: string;
  research_purpose: string;
  asset_affordance_tags: string[];
  readiness_verdict: string;
};

export type AtlasReadinessWarning = {
  label: string;
  detail: string;
  severity: 'warning' | 'blocker' | 'info';
};

export type AtlasReadinessPanelPreview = {
  warnings: AtlasReadinessWarning[];
  warning_count: number;
  readiness_surfaces: Record<string, { status: string; reason: string }>;
};

export type AtlasGapsNextMovePanel = {
  top_blockers: string[];
  graph_health_warnings: string[];
  next_recommended_packet: string;
  recommender_reason: string;
};

export type AtlasGraphSummaryPanelPreview = {
  relationship_density: number;
  relationship_count: number;
  edge_type_counts: Record<string, number>;
  clustered_atom_count: number;
  weak_atom_count: number;
  multi_claim_atom_count: number;
  source_diverse_atom_count: number;
  orphan_claim_count: number;
  orphan_atom_count: number;
  synthesis_ready_cluster_count: number;
  frontend_ready_trace_count: number;
  graph_readiness_verdict: string;
  top_graph_blockers: string[];
  next_recommended_packet: string;
  recommender_reason: string;
};

export type AtlasTracePanelRow = {
  trace_ref: string;
  source_status: string;
  claim_summary: string;
  atom_ref: string;
  concept_links: string[];
  relationship_links: string[];
  cluster_link: string;
  public_safe_connection_explanation: string;
};

export type AtlasTracePanelPreview = {
  trace_count: number;
  frontend_ready_trace_count: number;
  atom_count: number;
  accepted_claim_count: number;
  trace_details: AtlasTracePanelRow[];
};

export type TinyAtlasConnectionPreview = {
  schema_version: string;
  generated_at: string;
  source_snapshot_id: string;
  source_audit_report: string;
  public_safe: boolean;
  question: {
    topic: string;
    primary_question: string;
    research_purpose: string;
    asset_affordance_tags: string[];
    readiness_verdict: string;
  };
  source_health: AtlasSourceHealthPanel;
  cluster: {
    cluster_id: string;
    cluster_name: string;
    maturity: string;
    synthesis_readiness: string;
    relationship_density: number;
    relationship_density_threshold: number;
    low_relationship_density: boolean;
    source_diversity: number;
    claims_per_cluster: number;
    atoms_per_cluster: number;
    relationships_per_cluster: number;
    orphan_claim_count: number;
    orphan_atom_count: number;
    warning: string;
  };
  evidence_atoms: Array<{
    atom_ref: string;
    canonical_atom_text: string;
    maturity: string;
    support_count: number;
    contradiction_count: number;
    qualification_count: number;
    source_count: number;
    purpose_match_status: string;
    asset_tags: string[];
    why_clustered: string;
    why_weak: string;
  }>;
  relationships: Array<{
    relationship_ref: string;
    type: string;
    connected_concepts: string[];
    summary: string;
    explanation: string;
  }>;
  trace_details: Array<{
    trace_ref: string;
    source_status: string;
    claim_summary: string;
    atom_ref: string;
    concept_links: string[];
    relationship_links: string[];
    cluster_link: string;
    public_safe_connection_explanation: string;
  }>;
  readiness: Record<string, { status: string; reason: string }>;
  gaps_next_move: {
    top_blockers: string[];
    graph_health_warnings: string[];
    next_recommended_packet: string;
    recommender_reason: string;
  };
};

export const atlasSnapshot = snapshot as AtlasPreviewSnapshot;
export const atlasCoherence = coherence as AtlasCoherencePreview;
export const tinyAtlasConnectionPreview =
  connectionPreview as TinyAtlasConnectionPreview;
export const atlasSourceHealthRunArtifact =
  sourceHealthRun as AtlasSourceHealthRunArtifact;

const ATLAS_SOURCE_HEALTH_RUN_SCHEMA = 'atlas_source_health_run_v0.1.0';

export function mapRunArtifactToSourceHealthPanel(
  artifact: AtlasSourceHealthRunArtifact,
): AtlasSourceHealthPanel {
  const summary = artifact.source_health_summary;
  return {
    source_counts_by_status: summary.source_status_counts,
    acquisition_parser_status: Object.entries(summary.parser_backend_counts).map(
      ([status, count]) => ({
        status,
        count,
        note: 'Parser backend from Atlas-safe source-health run artifact.',
      }),
    ),
    quality_gate_outcomes: Object.entries(summary.quality_gate_status_counts).map(
      ([outcome, count]) => ({ outcome, count }),
    ),
    blocked_dirty_failed_reasons: Object.entries(summary.failure_reason_counts).map(
      ([reason, count]) => ({ reason, count }),
    ),
  };
}

/** Prefer Atlas-safe run artifact source health; fall back to tiny connection preview. */
export function resolveSourceHealthPreview(): AtlasSourceHealthPanel & {
  preview_source: 'run_artifact' | 'fixture';
} {
  if (atlasSourceHealthRunArtifact.schema_version === ATLAS_SOURCE_HEALTH_RUN_SCHEMA) {
    return {
      ...mapRunArtifactToSourceHealthPanel(atlasSourceHealthRunArtifact),
      preview_source: 'run_artifact',
    };
  }
  return {
    ...tinyAtlasConnectionPreview.source_health,
    preview_source: 'fixture',
  };
}

export function mapRunArtifactToGapsNextMovePanel(
  artifact: AtlasSourceHealthRunArtifact,
): AtlasGapsNextMovePanel {
  const summary = artifact.source_health_summary;
  const failureReasons = summary.failure_reason_counts || {};
  const topBlockers = Object.entries(failureReasons).map(
    ([reason, count]) => `${humanizeLabel(reason)} (${count})`,
  );
  const readinessWarnings = list(artifact.readiness_warnings);
  return {
    top_blockers:
      topBlockers.length > 0
        ? topBlockers
        : readinessWarnings.slice(0, 2),
    graph_health_warnings: readinessWarnings,
    next_recommended_packet:
      artifact.next_recommended_packet || 'source-health-persistence',
    recommender_reason:
      artifact.next_recommended_reason ||
      'Run artifact did not include a recommender rationale.',
  };
}

function list(values: string[] | undefined): string[] {
  return Array.isArray(values) ? values.filter(Boolean) : [];
}

/** Prefer Atlas-safe run artifact gaps; fall back to tiny connection preview. */
export function resolveGapsNextMovePreview(): AtlasGapsNextMovePanel & {
  preview_source: 'run_artifact' | 'fixture';
} {
  if (atlasSourceHealthRunArtifact.schema_version === ATLAS_SOURCE_HEALTH_RUN_SCHEMA) {
    return {
      ...mapRunArtifactToGapsNextMovePanel(atlasSourceHealthRunArtifact),
      preview_source: 'run_artifact',
    };
  }
  return {
    ...tinyAtlasConnectionPreview.gaps_next_move,
    preview_source: 'fixture',
  };
}

export function mapRunArtifactToReadinessPanel(
  artifact: AtlasSourceHealthRunArtifact,
): AtlasReadinessPanelPreview {
  const warnings = list(artifact.readiness_warnings).map((detail) => ({
    label: 'Run readiness',
    detail,
    severity: detail.toLowerCase().includes('blocker') ? 'blocker' as const : 'warning' as const,
  }));
  return {
    warnings,
    warning_count: warnings.length,
    readiness_surfaces: {},
  };
}

function mapFixtureReadinessSurfaces(): Record<string, { status: string; reason: string }> {
  const surfaces = tinyAtlasConnectionPreview.readiness || {};
  return Object.fromEntries(
    Object.entries(surfaces).map(([surface, readiness]) => [
      surface,
      { status: readiness.status, reason: readiness.reason },
    ]),
  );
}

/** Prefer Atlas-safe run artifact readiness warnings; fall back to fixture surfaces. */
export function resolveReadinessPanelPreview(): AtlasReadinessPanelPreview & {
  preview_source: 'run_artifact' | 'fixture';
} {
  if (atlasSourceHealthRunArtifact.schema_version === ATLAS_SOURCE_HEALTH_RUN_SCHEMA) {
    return {
      ...mapRunArtifactToReadinessPanel(atlasSourceHealthRunArtifact),
      preview_source: 'run_artifact',
    };
  }
  const surfaces = mapFixtureReadinessSurfaces();
  const warnings = Object.entries(surfaces).map(([surface, readiness]) => ({
    label: humanizeLabel(surface),
    detail: `${readiness.status}: ${readiness.reason}`,
    severity:
      readiness.status === 'NO-GO'
        ? ('blocker' as const)
        : readiness.status === 'PARTIAL'
          ? ('warning' as const)
          : ('info' as const),
  }));
  return {
    warnings,
    warning_count: warnings.length,
    readiness_surfaces: surfaces,
    preview_source: 'fixture',
  };
}

export function mapRunArtifactToPurposePanel(
  artifact: AtlasSourceHealthRunArtifact,
): AtlasPurposePanelPreview {
  const purpose = artifact.purpose || {};
  const purposeFit = artifact.source_health_summary.purpose_fit_status_counts || {};
  const gateCounts = artifact.purpose_fit_summary?.gate_decision_counts || {};
  return {
    domain_pack: artifact.domain_pack,
    research_intents: list(purpose.research_intent).map((item) => humanizeLabel(item)),
    asset_affordances: list(purpose.asset_affordance).map((item) => humanizeLabel(item)),
    evidence_maturity: humanizeLabel(purpose.evidence_maturity || 'seed'),
    training_suitability: humanizeLabel(purpose.training_suitability || 'not_ready'),
    evidence_need: humanizeLabel(purpose.evidence_need || 'mixed_empirical_theory'),
    acceptable_source_types: list(purpose.acceptable_source_types).map((item) =>
      humanizeLabel(item),
    ),
    output_targets: list(purpose.output_targets).map((item) => humanizeLabel(item)),
    purpose_fit_counts: Object.fromEntries(
      Object.entries(purposeFit).map(([key, count]) => [humanizeLabel(key), count]),
    ),
    gate_decision_counts: Object.fromEntries(
      Object.entries(gateCounts).map(([key, count]) => [humanizeLabel(key), count]),
    ),
  };
}

/** Prefer Atlas-safe run artifact purpose metadata; fall back to fixture question block. */
export function resolvePurposePanelPreview(): AtlasPurposePanelPreview & {
  preview_source: 'run_artifact' | 'fixture';
} {
  if (atlasSourceHealthRunArtifact.schema_version === ATLAS_SOURCE_HEALTH_RUN_SCHEMA) {
    return {
      ...mapRunArtifactToPurposePanel(atlasSourceHealthRunArtifact),
      preview_source: 'run_artifact',
    };
  }
  const fixture = tinyAtlasConnectionPreview.question;
  return {
    domain_pack: fixture.topic,
    research_intents: fixture.research_purpose.split(' · ').filter(Boolean),
    asset_affordances: fixture.asset_affordance_tags.map((item) => humanizeLabel(item)),
    evidence_maturity: 'Seed',
    training_suitability: 'Not ready',
    evidence_need: 'Mixed empirical theory',
    acceptable_source_types: [],
    output_targets: [],
    purpose_fit_counts: {},
    gate_decision_counts: {},
    preview_source: 'fixture',
  };
}

function graphWarningMatches(text: string): boolean {
  const lowered = text.toLowerCase();
  return (
    lowered.includes('relationship') ||
    lowered.includes('graph') ||
    lowered.includes('atom') ||
    lowered.includes('cluster') ||
    lowered.includes('orphan') ||
    lowered.includes('edge') ||
    lowered.includes('density')
  );
}

function deriveGraphReadinessVerdict(input: {
  relationship_count: number;
  weak_atom_count: number;
  orphan_claim_count: number;
  orphan_atom_count: number;
  low_relationship_density: boolean;
}): string {
  if (input.relationship_count <= 0) {
    return 'NO-GO — no relationship graph produced';
  }
  if (
    input.low_relationship_density ||
    input.weak_atom_count > 0 ||
    input.orphan_claim_count > 0 ||
    input.orphan_atom_count > 0
  ) {
    return 'PARTIAL — graph exists but clustering/density gaps remain';
  }
  return 'PASS — graph connection metrics meet preview thresholds';
}

export function mapRunArtifactToGraphSummaryPanel(
  artifact: AtlasSourceHealthRunArtifact,
): AtlasGraphSummaryPanelPreview {
  const graph = artifact.graph_summary || {};
  const metrics = graph.connection_metrics || {};
  const totals = metrics.totals || {};
  const clusters = metrics.clusters || [];
  const relationshipCount = Number(totals.relationships ?? graph.relationships ?? 0);
  const claimCount = Number(totals.claims ?? graph.claims ?? 0);
  const clusterDensity = clusters.map((cluster) => Number(cluster.relationship_density ?? 0));
  const relationshipDensity =
    claimCount > 0
      ? relationshipCount / claimCount
      : clusterDensity.length > 0
        ? clusterDensity.reduce((sum, value) => sum + value, 0) / clusterDensity.length
        : 0;
  const contradicts = Number(totals.contradiction_edge_count ?? 0);
  const qualifies = Number(totals.qualification_edge_count ?? 0);
  const supports = Math.max(0, relationshipCount - contradicts - qualifies);
  const lowRelationshipDensity = clusters.some(
    (cluster) => cluster.low_relationship_density === true,
  );
  const readinessWarnings = list(artifact.readiness_warnings).filter(graphWarningMatches);
  const derivedBlockers: string[] = [];
  if (relationshipCount <= 0) {
    derivedBlockers.push('No relationship graph was produced for this run.');
  }
  if (lowRelationshipDensity) {
    derivedBlockers.push('At least one cluster reports low relationship density.');
  }
  if (Number(totals.weak_atom_count ?? 0) > 0) {
    derivedBlockers.push(
      `${totals.weak_atom_count} evidence atom(s) remain weak or seed maturity.`,
    );
  }
  if (Number(totals.orphan_claim_count ?? 0) > 0) {
    derivedBlockers.push(
      `${totals.orphan_claim_count} orphan claim(s) lack relationship coverage.`,
    );
  }
  if (Number(totals.orphan_atom_count ?? 0) > 0) {
    derivedBlockers.push(
      `${totals.orphan_atom_count} orphan atom(s) lack relationship coverage.`,
    );
  }
  const topGraphBlockers = [...new Set([...readinessWarnings, ...derivedBlockers])].slice(0, 6);
  return {
    relationship_density: Number(relationshipDensity.toFixed(4)),
    relationship_count: relationshipCount,
    edge_type_counts: {
      supports,
      contradicts,
      qualifies,
    },
    clustered_atom_count: Number(totals.clustered_atom_count ?? 0),
    weak_atom_count: Number(totals.weak_atom_count ?? 0),
    multi_claim_atom_count: Number(totals.multi_claim_atom_count ?? 0),
    source_diverse_atom_count: Number(totals.source_diverse_atom_count ?? 0),
    orphan_claim_count: Number(totals.orphan_claim_count ?? 0),
    orphan_atom_count: Number(totals.orphan_atom_count ?? 0),
    synthesis_ready_cluster_count: Number(totals.synthesis_ready_cluster_count ?? 0),
    frontend_ready_trace_count: Number(totals.frontend_ready_trace_count ?? 0),
    graph_readiness_verdict: deriveGraphReadinessVerdict({
      relationship_count: relationshipCount,
      weak_atom_count: Number(totals.weak_atom_count ?? 0),
      orphan_claim_count: Number(totals.orphan_claim_count ?? 0),
      orphan_atom_count: Number(totals.orphan_atom_count ?? 0),
      low_relationship_density: lowRelationshipDensity,
    }),
    top_graph_blockers: topGraphBlockers,
    next_recommended_packet:
      artifact.next_recommended_packet || 'graph-connection-metrics',
    recommender_reason:
      artifact.next_recommended_reason ||
      'Run artifact did not include a graph recommender rationale.',
  };
}

function mapFixtureGraphSummaryPanel(): AtlasGraphSummaryPanelPreview {
  const cluster = tinyAtlasConnectionPreview.cluster;
  const atoms = tinyAtlasConnectionPreview.evidence_atoms;
  const relationships = tinyAtlasConnectionPreview.relationships;
  const traces = tinyAtlasConnectionPreview.trace_details;
  const gaps = tinyAtlasConnectionPreview.gaps_next_move;
  const edgeTypeCounts = relationships.reduce<Record<string, number>>((counts, relationship) => {
    const key = humanizeLabel(relationship.type);
    counts[key] = (counts[key] || 0) + 1;
    return counts;
  }, {});
  const clusteredAtomCount = atoms.filter((atom) =>
    ['clustered', 'synthesis_ready', 'eval_ready', 'training_ready'].includes(atom.maturity),
  ).length;
  const weakAtomCount = atoms.filter((atom) =>
    ['seed', 'weak', 'promising'].includes(atom.maturity),
  ).length;
  const multiClaimAtomCount = atoms.filter((atom) =>
    /clusters?\s+\d+\s+compatible claim/i.test(atom.why_clustered || ''),
  ).length;
  const sourceDiverseAtomCount = atoms.filter((atom) => atom.source_count >= 2).length;
  const topGraphBlockers = [
    ...gaps.graph_health_warnings,
    ...gaps.top_blockers.filter(graphWarningMatches),
  ].slice(0, 6);
  return {
    relationship_density: cluster.relationship_density,
    relationship_count: cluster.relationships_per_cluster,
    edge_type_counts: edgeTypeCounts,
    clustered_atom_count: clusteredAtomCount,
    weak_atom_count: weakAtomCount,
    multi_claim_atom_count: multiClaimAtomCount,
    source_diverse_atom_count: sourceDiverseAtomCount,
    orphan_claim_count: cluster.orphan_claim_count,
    orphan_atom_count: cluster.orphan_atom_count,
    synthesis_ready_cluster_count: cluster.synthesis_readiness.includes('ready') ? 1 : 0,
    frontend_ready_trace_count: traces.length,
    graph_readiness_verdict: cluster.low_relationship_density
      ? 'PARTIAL — fixture cluster density below threshold'
      : 'PARTIAL — fixture-backed graph preview only',
    top_graph_blockers: topGraphBlockers,
    next_recommended_packet: gaps.next_recommended_packet,
    recommender_reason: gaps.recommender_reason,
  };
}

/** Prefer Atlas-safe run artifact graph summary; fall back to fixture cluster graph block. */
export function resolveGraphSummaryPanelPreview(): AtlasGraphSummaryPanelPreview & {
  preview_source: 'run_artifact' | 'fixture';
} {
  if (atlasSourceHealthRunArtifact.schema_version === ATLAS_SOURCE_HEALTH_RUN_SCHEMA) {
    return {
      ...mapRunArtifactToGraphSummaryPanel(atlasSourceHealthRunArtifact),
      preview_source: 'run_artifact',
    };
  }
  return {
    ...mapFixtureGraphSummaryPanel(),
    preview_source: 'fixture',
  };
}

export function mapRunArtifactToQuestionHeader(
  artifact: AtlasSourceHealthRunArtifact,
): AtlasQuestionHeaderPreview {
  const purpose = artifact.purpose || {};
  const intents = list(purpose.research_intent);
  const affordances = list(purpose.asset_affordance);
  const maturity = purpose.evidence_maturity || 'seed';
  const training = purpose.training_suitability || 'not_ready';
  return {
    topic: artifact.domain_pack,
    primary_question: artifact.question,
    research_purpose:
      intents.length > 0
        ? intents.map((item) => humanizeLabel(item)).join(' · ')
        : 'Research review',
    asset_affordance_tags: affordances.map((item) => humanizeLabel(item)),
    readiness_verdict: `PARTIAL — ${humanizeLabel(maturity)} evidence / ${humanizeLabel(training)} training`,
  };
}

/** Prefer Atlas-safe run artifact question header; fall back to tiny connection preview. */
export function resolveQuestionHeaderPreview(): AtlasQuestionHeaderPreview & {
  preview_source: 'run_artifact' | 'fixture';
  page_title: string;
  page_subtitle: string;
} {
  if (atlasSourceHealthRunArtifact.schema_version === ATLAS_SOURCE_HEALTH_RUN_SCHEMA) {
    const header = mapRunArtifactToQuestionHeader(atlasSourceHealthRunArtifact);
    return {
      ...header,
      preview_source: 'run_artifact',
      page_title: header.primary_question,
      page_subtitle: 'Atlas-safe source-health run artifact preview',
    };
  }
  const fixture = tinyAtlasConnectionPreview.question;
  return {
    ...fixture,
    preview_source: 'fixture',
    page_title: atlasSnapshot.root.primary_question,
    page_subtitle: 'Research Atlas · staged-spine mock preview',
  };
}

/** Prefer inline snapshot coherence_summary; fall back to separate preview JSON. */
export function resolveAtlasCoherencePreview(): AtlasCoherenceSummary & {
  population: Record<string, number>;
} {
  if (atlasSnapshot.coherence_summary) {
    return {
      ...atlasSnapshot.coherence_summary,
      population: atlasCoherence.population,
    };
  }
  return {
    overall_coherence_verdict: atlasCoherence.overall_coherence_verdict,
    preview_label: atlasCoherence.preview_label,
    population: atlasCoherence.population,
  };
}

/** Prefer Atlas-safe run artifact trace rows; fall back to fixture trace details. */
export function mapRunArtifactTraceRow(
  trace: NonNullable<
    NonNullable<AtlasSourceHealthRunArtifact['trace_summary']>['atlas_trace_preview']
  >[number],
): AtlasTracePanelRow {
  const relationshipTypes = list(trace.relationship_types);
  const relationshipType = String(trace.relationship_type || '');
  const relationshipLinks =
    relationshipTypes.length > 0
      ? relationshipTypes.map((item) => humanizeLabel(item))
      : relationshipType
        ? [humanizeLabel(relationshipType)]
        : [];
  const conceptCount = Number(trace.concept_count ?? 0);
  return {
    trace_ref: String(trace.trace_ref || 'trace_unknown'),
    source_status: String(trace.purpose_match_status || 'live_abstract'),
    claim_summary:
      String(trace.why_connected || trace.why_clustered || '').trim() ||
      'Quote-backed abstract evidence trace',
    atom_ref: trace.has_quote ? 'atom_present' : 'atom_pending',
    concept_links:
      conceptCount > 0 ? [`${conceptCount} linked concept(s)`] : ['concepts pending'],
    relationship_links: relationshipLinks.length > 0 ? relationshipLinks : ['relationships pending'],
    cluster_link: String(trace.atom_cluster_maturity || 'seed'),
    public_safe_connection_explanation:
      String(trace.why_connected || trace.why_clustered || '').trim() ||
      'Live abstract evidence trace preview without private row IDs or raw quote text.',
  };
}

export function mapRunArtifactToTracePanel(
  artifact: AtlasSourceHealthRunArtifact,
): AtlasTracePanelPreview {
  const summary = artifact.trace_summary || {};
  const rows = (summary.atlas_trace_preview ?? []).map(mapRunArtifactTraceRow);
  return {
    trace_count: Number(summary.trace_count ?? rows.length),
    frontend_ready_trace_count: Number(
      summary.frontend_ready_trace_count ?? rows.length,
    ),
    atom_count: Number(summary.atom_count ?? 0),
    accepted_claim_count: Number(summary.accepted_claim_count ?? 0),
    trace_details: rows,
  };
}

function mapFixtureTracePanel(): AtlasTracePanelPreview {
  const traces = tinyAtlasConnectionPreview.trace_details;
  return {
    trace_count: traces.length,
    frontend_ready_trace_count: traces.length,
    atom_count: tinyAtlasConnectionPreview.evidence_atoms.length,
    accepted_claim_count: tinyAtlasConnectionPreview.cluster.claims_per_cluster,
    trace_details: traces,
  };
}

export function resolveTracePanelPreview(): AtlasTracePanelPreview & {
  preview_source: 'run_artifact' | 'fixture';
} {
  if (atlasSourceHealthRunArtifact.schema_version === ATLAS_SOURCE_HEALTH_RUN_SCHEMA) {
    const panel = mapRunArtifactToTracePanel(atlasSourceHealthRunArtifact);
    if (panel.trace_details.length > 0) {
      return { ...panel, preview_source: 'run_artifact' };
    }
  }
  return { ...mapFixtureTracePanel(), preview_source: 'fixture' };
}

export function coherenceBadgeColor(verdict: string): string {
  if (verdict === 'pass') {
    return '#3d8f6a';
  }
  if (verdict === 'partial') {
    return '#c9a227';
  }
  return '#b85c5c';
}

export function formatEdgeSummary(edge: AtlasPreviewEdge): string {
  const scope = edge.scope ? ` (${edge.scope})` : '';
  return `${edge.source_label} ${humanizeLabel(edge.predicate)} ${edge.target_label}${scope}`;
}

export { formatPublicTimestamp, humanizeLabel };
