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
  purpose?: {
    research_intent?: string[];
    asset_affordance?: string[];
    evidence_maturity?: string;
    training_suitability?: string;
    evidence_need?: string;
    acceptable_source_types?: string[];
    output_targets?: string[];
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
