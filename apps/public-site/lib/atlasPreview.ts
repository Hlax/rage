import snapshot from '../public/data/atlas_snapshot_preview.json';
import coherence from '../public/data/atlas_coherence_preview.json';
import connectionPreview from '../public/data/tiny_atlas_connection_preview.json';
import sourceHealthRun from '../public/data/atlas_source_health_run_latest.json';
import multiQuestionLiveAbstract from '../public/data/atlas_multi_question_live_abstract_latest.json';
import localModelExtractionComparison from '../public/data/atlas_local_model_extraction_comparison_latest.json';
import graphMaturityUpgrade from '../public/data/atlas_graph_maturity_evidence_atom_upgrade_latest.json';
import webAdapterScraplingProof from '../public/data/atlas_web_adapter_scrapling_proof_latest.json';
import pdfTeiMilestone from '../public/data/atlas_pdf_tei_milestone_latest.json';
import demoLoopPolish from '../public/data/atlas_demo_loop_polish_latest.json';
import fullAtlasRefreshChecklist from '../public/data/atlas_full_atlas_refresh_checklist_latest.json';
import openaiSynthesisAdapterSpec from '../public/data/atlas_openai_synthesis_adapter_spec_latest.json';
import synthesisHumanReview from '../public/data/atlas_synthesis_human_review_latest.json';
import releaseGovernor from '../public/data/atlas_release_governor_latest.json';
import tier2PatchStaging from '../public/data/atlas_tier2_patch_staging_latest.json';

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
  resolver_breakdown: Array<{ backend: string; count: number; note: string }>;
};

export type AtlasLiveSourceExpansionPanel = {
  verdict: string;
  rationale: string;
  discovery_backends: string[];
  enrich_unpaywall: boolean;
  source_diversity_count: number;
  doi_backed_count: number;
  unpaywall_enriched_count: number;
  resolved_count: number;
  discovery_breakdown: Array<{ backend: string; count: number }>;
  persisted_breakdown: Array<{ backend: string; count: number }>;
  unpaywall_skipped: Array<{ reason: string; count: number }>;
  blocked_sources_visible: boolean;
};

export type AtlasLocalModelExtractionComparisonArtifact = {
  schema_version: string;
  status: string;
  packet_id: string;
  comparison_verdict: string;
  comparison_rationale: string;
  evaluation_only: boolean;
  ollama_model?: string | null;
  comparison_aggregate: {
    compared_abstract_count: number;
    mock_total_accepted: number;
    local_ollama_total_accepted: number;
    mock_quote_validity_rate: number | null;
    local_ollama_quote_validity_rate: number | null;
    quality_vs_mock_overall: string;
    local_thinner_count?: number;
    local_better_count?: number;
    ollama_rejection_reason_totals?: Record<string, number>;
  };
  abstract_comparisons: Array<{
    source_ref: string;
    resolver_backend: string;
    abstract_char_count: number;
    comparison: {
      quality_vs_mock: string;
      accepted_delta: number;
      local_thinner_than_mock: boolean;
    };
    mock_deterministic: {
      accepted_count: number;
      rejected_count: number;
      quote_validity_rate: number | null;
    };
    local_ollama: {
      accepted_count: number;
      rejected_count: number;
      quote_validity_rate: number | null;
      rejection_reason_counts?: Record<string, number>;
    };
  }>;
  local_model_readiness?: {
    status: string;
    notes: string;
  };
};

export type AtlasLocalModelExtractionPanel = {
  comparison_verdict: string;
  comparison_rationale: string;
  ollama_model: string;
  quality_vs_mock_overall: string;
  compared_abstract_count: number;
  mock_total_accepted: number;
  local_ollama_total_accepted: number;
  mock_quote_validity_rate: string;
  local_ollama_quote_validity_rate: string;
  per_abstract_rows: Array<{
    source_ref: string;
    resolver_backend: string;
    quality_vs_mock: string;
    mock_accepted: number;
    ollama_accepted: number;
  }>;
  ollama_rejection_totals: Array<{ reason: string; count: number }>;
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
    resolver_source_counts?: Record<string, number>;
    enrichment_backend_counts?: Record<string, number>;
    sources_with_metadata: number;
  };
  source_expansion_summary?: {
    discovery_backends?: string[];
    enrich_unpaywall?: boolean;
    resolver_breakdown?: Record<string, number>;
    persisted_resolver_source_counts?: Record<string, number>;
    source_diversity_count?: number;
    doi_backed_count?: number;
    unpaywall_enriched_count?: number;
    unpaywall_skipped_counts?: Record<string, number>;
    blocked_source_reason_counts?: Record<string, number>;
    blocked_sources_visible?: boolean;
    resolved_count?: number;
  };
  source_expansion_verdict?: string;
  source_expansion_rationale?: string;
  packet_id?: string;
  readiness_warnings?: string[];
  next_recommended_packet?: string | { id: string; title: string };
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
export const atlasLocalModelExtractionComparisonArtifact =
  localModelExtractionComparison as AtlasLocalModelExtractionComparisonArtifact;

export type AtlasGraphMaturityUpgradeArtifact = {
  schema_version: string;
  status: string;
  packet_id: string;
  graph_maturity_verdict: string;
  graph_maturity_rationale: string;
  question_count: number;
  total_accepted_claims: number;
  maturity_before: Record<string, number | null>;
  maturity_after: Record<string, number | null>;
  maturity_delta: Record<string, number>;
  cluster_maturity_explanations: Array<{
    cluster_ref: string;
    maturity_label: string;
    relationship_density: number;
    orphan_claim_count: number;
    reasons: string[];
  }>;
};

export type AtlasGraphMaturityPanel = {
  verdict: string;
  rationale: string;
  question_count: number;
  total_accepted_claims: number;
  before_single_claim_atoms: number;
  after_single_claim_atoms: number;
  before_clustered_atoms: number;
  after_clustered_atoms: number;
  relationship_density_before: string;
  relationship_density_after: string;
  cluster_explanations: AtlasGraphMaturityUpgradeArtifact['cluster_maturity_explanations'];
};

export const atlasGraphMaturityUpgradeArtifact =
  graphMaturityUpgrade as AtlasGraphMaturityUpgradeArtifact;

const ATLAS_SOURCE_HEALTH_RUN_SCHEMA = 'atlas_source_health_run_v0.1.0';
const ATLAS_LOCAL_MODEL_EXTRACTION_COMPARISON_SCHEMA =
  'atlas_local_model_extraction_comparison_v0.1.0';
const ATLAS_GRAPH_MATURITY_UPGRADE_SCHEMA =
  'atlas_graph_maturity_evidence_atom_upgrade_v0.1.0';

export function mapRunArtifactToSourceHealthPanel(
  artifact: AtlasSourceHealthRunArtifact,
): AtlasSourceHealthPanel {
  const summary = artifact.source_health_summary;
  const expansion = artifact.source_expansion_summary;
  const resolverCounts =
    expansion?.persisted_resolver_source_counts ||
    summary.resolver_source_counts ||
    {};
  const discoveryBreakdown = expansion?.resolver_breakdown || {};
  const resolverEntries = Object.keys(resolverCounts).length
    ? Object.entries(resolverCounts)
    : Object.entries(discoveryBreakdown);
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
    resolver_breakdown: resolverEntries.map(([backend, count]) => ({
      backend,
      count,
      note:
        backend === 'unpaywall'
          ? 'Unpaywall OA enrichment backend.'
          : 'Discovery resolver backend from live source expansion.',
    })),
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

export function resolveLiveSourceExpansionPreview():
  | AtlasLiveSourceExpansionPanel
  | null {
  const artifact = atlasSourceHealthRunArtifact;
  if (artifact.schema_version !== ATLAS_SOURCE_HEALTH_RUN_SCHEMA) {
    return null;
  }
  const expansion = artifact.source_expansion_summary;
  if (!expansion) {
    return null;
  }
  const discoveryBreakdown = expansion.resolver_breakdown || {};
  const persistedBreakdown = expansion.persisted_resolver_source_counts || {};
  return {
    verdict: artifact.source_expansion_verdict || 'unknown',
    rationale:
      artifact.source_expansion_rationale ||
      'Live OpenAlex/arXiv discovery with optional Unpaywall DOI/OA enrichment.',
    discovery_backends: expansion.discovery_backends || [],
    enrich_unpaywall: Boolean(expansion.enrich_unpaywall),
    source_diversity_count: expansion.source_diversity_count || 0,
    doi_backed_count: expansion.doi_backed_count || 0,
    unpaywall_enriched_count: expansion.unpaywall_enriched_count || 0,
    resolved_count: expansion.resolved_count || 0,
    discovery_breakdown: Object.entries(discoveryBreakdown).map(([backend, count]) => ({
      backend,
      count,
    })),
    persisted_breakdown: Object.entries(persistedBreakdown).map(([backend, count]) => ({
      backend,
      count,
    })),
    unpaywall_skipped: Object.entries(expansion.unpaywall_skipped_counts || {}).map(
      ([reason, count]) => ({ reason, count }),
    ),
    blocked_sources_visible: Boolean(expansion.blocked_sources_visible),
  };
}

function formatRate(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return 'n/a';
  }
  return `${Math.round(value * 100)}%`;
}

export type AtlasMultiQuestionLiveAbstractArtifact = {
  schema_version: string;
  status: string;
  packet_id: string;
  question_count: number;
  multi_question_verdict?: string;
  multi_question_rationale?: string;
  purpose_routing_validation: {
    purpose_routing_valid: boolean;
    strict_questions_reject_generic: boolean;
    open_questions_allow_generic: boolean;
  };
  question_runs: Array<{
    question_id: string;
    gate_mode: string;
    evidence_quality_verdict: string;
    live_source_count: number;
    claims_accepted: number;
    claims_rejected: number;
  }>;
  aggregate: {
    questions_with_live_sources: number;
    questions_with_accepted_claims: number;
    total_accepted_claims: number;
    total_rejected_claims: number;
  };
};

export type AtlasMultiQuestionLiveAbstractPanel = {
  verdict: string;
  rationale: string;
  question_count: number;
  purpose_routing_valid: boolean;
  questions_with_live_sources: number;
  questions_with_accepted_claims: number;
  total_accepted_claims: number;
  strict_gate_count: number;
  open_gate_count: number;
  per_question_rows: Array<{
    question_id: string;
    gate_mode: string;
    accepted: number;
    rejected: number;
    verdict: string;
  }>;
};

export const atlasMultiQuestionLiveAbstractArtifact =
  multiQuestionLiveAbstract as AtlasMultiQuestionLiveAbstractArtifact;

const ATLAS_MULTI_QUESTION_LIVE_ABSTRACT_SCHEMA =
  'atlas_multi_question_live_abstract_v0.1.0';

export function mapMultiQuestionArtifactToPanel(
  artifact: AtlasMultiQuestionLiveAbstractArtifact,
): AtlasMultiQuestionLiveAbstractPanel {
  const runs = artifact.question_runs || [];
  const aggregate = artifact.aggregate || {
    questions_with_live_sources: 0,
    questions_with_accepted_claims: 0,
    total_accepted_claims: 0,
    total_rejected_claims: 0,
  };
  const purpose = artifact.purpose_routing_validation || {
    purpose_routing_valid: false,
  };
  const inferredVerdict =
    aggregate.questions_with_accepted_claims >= 3 && purpose.purpose_routing_valid
      ? 'GO'
      : 'PARTIAL';
  return {
    verdict: artifact.multi_question_verdict || inferredVerdict,
    rationale:
      artifact.multi_question_rationale ||
      'Multi-question live abstract bundle synced to Atlas preview.',
    question_count: Number(artifact.question_count || runs.length),
    purpose_routing_valid: Boolean(purpose.purpose_routing_valid),
    questions_with_live_sources: Number(aggregate.questions_with_live_sources || 0),
    questions_with_accepted_claims: Number(
      aggregate.questions_with_accepted_claims || 0,
    ),
    total_accepted_claims: Number(aggregate.total_accepted_claims || 0),
    strict_gate_count: runs.filter((run) => run.gate_mode === 'strict').length,
    open_gate_count: runs.filter((run) => run.gate_mode === 'open').length,
    per_question_rows: runs.map((run) => ({
      question_id: run.question_id,
      gate_mode: run.gate_mode,
      accepted: Number(run.claims_accepted || 0),
      rejected: Number(run.claims_rejected || 0),
      verdict: run.evidence_quality_verdict,
    })),
  };
}

export function resolveMultiQuestionLiveAbstractPreview():
  | (AtlasMultiQuestionLiveAbstractPanel & { preview_source: 'run_artifact' })
  | null {
  if (
    atlasMultiQuestionLiveAbstractArtifact.schema_version !==
    ATLAS_MULTI_QUESTION_LIVE_ABSTRACT_SCHEMA
  ) {
    return null;
  }
  return {
    ...mapMultiQuestionArtifactToPanel(atlasMultiQuestionLiveAbstractArtifact),
    preview_source: 'run_artifact',
  };
}

export function mapComparisonArtifactToLocalModelPanel(
  artifact: AtlasLocalModelExtractionComparisonArtifact,
): AtlasLocalModelExtractionPanel {
  const aggregate = artifact.comparison_aggregate;
  const rows = artifact.abstract_comparisons || [];
  return {
    comparison_verdict: artifact.comparison_verdict,
    comparison_rationale: artifact.comparison_rationale || '',
    ollama_model: artifact.ollama_model || 'unknown',
    quality_vs_mock_overall: aggregate.quality_vs_mock_overall,
    compared_abstract_count: aggregate.compared_abstract_count,
    mock_total_accepted: aggregate.mock_total_accepted,
    local_ollama_total_accepted: aggregate.local_ollama_total_accepted,
    mock_quote_validity_rate: formatRate(aggregate.mock_quote_validity_rate),
    local_ollama_quote_validity_rate: formatRate(
      aggregate.local_ollama_quote_validity_rate,
    ),
    per_abstract_rows: rows.map((row) => ({
      source_ref: row.source_ref,
      resolver_backend: row.resolver_backend,
      quality_vs_mock: row.comparison.quality_vs_mock,
      mock_accepted: row.mock_deterministic.accepted_count,
      ollama_accepted: row.local_ollama.accepted_count,
    })),
    ollama_rejection_totals: Object.entries(
      aggregate.ollama_rejection_reason_totals || {},
    ).map(([reason, count]) => ({ reason, count })),
  };
}

export function resolveLocalModelExtractionComparisonPreview():
  | (AtlasLocalModelExtractionPanel & { preview_source: 'run_artifact' })
  | null {
  if (
    atlasLocalModelExtractionComparisonArtifact.schema_version !==
    ATLAS_LOCAL_MODEL_EXTRACTION_COMPARISON_SCHEMA
  ) {
    return null;
  }
  return {
    ...mapComparisonArtifactToLocalModelPanel(
      atlasLocalModelExtractionComparisonArtifact,
    ),
    preview_source: 'run_artifact',
  };
}

export function mapGraphMaturityArtifactToPanel(
  artifact: AtlasGraphMaturityUpgradeArtifact,
): AtlasGraphMaturityPanel {
  const before = artifact.maturity_before || {};
  const after = artifact.maturity_after || {};
  return {
    verdict: artifact.graph_maturity_verdict,
    rationale: artifact.graph_maturity_rationale,
    question_count: artifact.question_count,
    total_accepted_claims: artifact.total_accepted_claims,
    before_single_claim_atoms: Number(before.single_claim_atom_count ?? 0),
    after_single_claim_atoms: Number(after.single_claim_atom_count ?? 0),
    before_clustered_atoms: Number(before.clustered_atom_count ?? 0),
    after_clustered_atoms: Number(after.clustered_atom_count ?? 0),
    relationship_density_before: formatRate(
      typeof before.relationship_density === 'number'
        ? before.relationship_density
        : null,
    ),
    relationship_density_after: formatRate(
      typeof after.relationship_density === 'number'
        ? after.relationship_density
        : null,
    ),
    cluster_explanations: artifact.cluster_maturity_explanations || [],
  };
}

export function resolveGraphMaturityUpgradePreview():
  | (AtlasGraphMaturityPanel & { preview_source: 'run_artifact' })
  | null {
  if (
    atlasGraphMaturityUpgradeArtifact.schema_version !==
    ATLAS_GRAPH_MATURITY_UPGRADE_SCHEMA
  ) {
    return null;
  }
  return {
    ...mapGraphMaturityArtifactToPanel(atlasGraphMaturityUpgradeArtifact),
    preview_source: 'run_artifact',
  };
}

export type AtlasWebAdapterScraplingProofArtifact = {
  schema_version: string;
  status: string;
  packet_id: string;
  web_adapter_verdict: string;
  web_adapter_rationale: string;
  fixture_ref: string;
  parser_comparison: {
    scrapling_available: boolean;
    html_to_text?: { text_length: number; parser_backend?: string };
    scrapling?: {
      text_length: number;
      parser_backend?: string;
      fallback_reason?: string | null;
      scrapling_used?: boolean;
    };
  };
  parser_backend_summary: {
    parser_backend?: string;
    acquisition_status?: string;
    extractable?: boolean;
    quoteable_span_count?: number;
    text_length?: number;
  };
  fixture_spine_summary: {
    status?: string;
    accepted_count: number;
    rejected_count: number;
    evidence_atom_count: number;
    relationship_count: number;
    acquisition_status?: string;
    quality_gate_passed?: boolean;
    trace_summary: {
      trace_count: number;
      atom_count: number;
      preview_row_count?: number;
    };
  };
  live_fetch_summary?: {
    status: string;
    reason?: string;
    extractable?: boolean;
  };
};

export type AtlasWebAdapterScraplingPanel = {
  verdict: string;
  rationale: string;
  parser_backend: string;
  scrapling_available: boolean;
  acquisition_status: string;
  quality_gate_passed: boolean;
  accepted_count: number;
  trace_count: number;
  evidence_atom_count: number;
  relationship_count: number;
  html_to_text_length: number;
  scrapling_text_length: number;
  live_fetch_status: string;
};

export const atlasWebAdapterScraplingProofArtifact =
  webAdapterScraplingProof as AtlasWebAdapterScraplingProofArtifact;

const ATLAS_WEB_ADAPTER_SCRAPLING_PROOF_SCHEMA =
  'atlas_web_adapter_scrapling_proof_v0.1.0';

export function mapWebAdapterArtifactToPanel(
  artifact: AtlasWebAdapterScraplingProofArtifact,
): AtlasWebAdapterScraplingPanel {
  const spine = artifact.fixture_spine_summary || {
    accepted_count: 0,
    rejected_count: 0,
    evidence_atom_count: 0,
    relationship_count: 0,
    trace_summary: { trace_count: 0, atom_count: 0 },
  };
  const parser = artifact.parser_backend_summary || {};
  const comparison = artifact.parser_comparison || { scrapling_available: false };
  return {
    verdict: artifact.web_adapter_verdict,
    rationale: artifact.web_adapter_rationale,
    parser_backend: String(parser.parser_backend || 'html_to_text'),
    scrapling_available: Boolean(comparison.scrapling_available),
    acquisition_status: String(
      parser.acquisition_status || spine.acquisition_status || 'unknown',
    ),
    quality_gate_passed: Boolean(spine.quality_gate_passed),
    accepted_count: Number(spine.accepted_count || 0),
    trace_count: Number(spine.trace_summary?.trace_count || 0),
    evidence_atom_count: Number(spine.evidence_atom_count || 0),
    relationship_count: Number(spine.relationship_count || 0),
    html_to_text_length: Number(comparison.html_to_text?.text_length || 0),
    scrapling_text_length: Number(comparison.scrapling?.text_length || 0),
    live_fetch_status: String(
      artifact.live_fetch_summary?.status || 'skipped',
    ),
  };
}

export function resolveWebAdapterScraplingProofPreview():
  | (AtlasWebAdapterScraplingPanel & { preview_source: 'run_artifact' })
  | null {
  if (
    atlasWebAdapterScraplingProofArtifact.schema_version !==
    ATLAS_WEB_ADAPTER_SCRAPLING_PROOF_SCHEMA
  ) {
    return null;
  }
  return {
    ...mapWebAdapterArtifactToPanel(atlasWebAdapterScraplingProofArtifact),
    preview_source: 'run_artifact',
  };
}

export type AtlasPdfTeiMilestoneArtifact = {
  schema_version: string;
  status: string;
  packet_id: string;
  pdf_tei_verdict: string;
  pdf_tei_rationale: string;
  tei_fixture_ref: string;
  pdf_fixture_ref: string;
  tei_parse_summary: {
    source_status?: string;
    parser_backend?: string;
    quoteable_span_count?: number;
    extracted_char_count?: number;
  };
  pdf_parse_summary: {
    source_status?: string;
    parser_backend?: string;
    quoteable_span_count?: number;
    extracted_char_count?: number;
  };
  dirty_pdf_gate_summary: {
    llm_extraction_blocked?: boolean;
    quality_gate_passed?: boolean;
    source_status?: string;
  };
  tei_spine_summary: {
    accepted_count: number;
    rejected_count: number;
    evidence_atom_count: number;
    relationship_count: number;
    quality_gate_passed?: boolean;
    trace_summary: { trace_count: number; atom_count: number };
  };
  pdf_spine_summary: {
    status?: string;
    accepted_count: number;
    trace_summary: { trace_count: number; atom_count: number };
  };
};

export type AtlasPdfTeiMilestonePanel = {
  verdict: string;
  rationale: string;
  tei_parser_backend: string;
  pdf_parser_backend: string;
  tei_quality_gate_passed: boolean;
  dirty_pdf_blocked: boolean;
  tei_accepted_count: number;
  tei_trace_count: number;
  pdf_accepted_count: number;
  tei_quoteable_spans: number;
  pdf_quoteable_spans: number;
};

export const atlasPdfTeiMilestoneArtifact =
  pdfTeiMilestone as AtlasPdfTeiMilestoneArtifact;

const ATLAS_PDF_TEI_MILESTONE_SCHEMA = 'atlas_pdf_tei_milestone_v0.1.0';

export function mapPdfTeiArtifactToPanel(
  artifact: AtlasPdfTeiMilestoneArtifact,
): AtlasPdfTeiMilestonePanel {
  const teiSpine = artifact.tei_spine_summary || {
    accepted_count: 0,
    rejected_count: 0,
    evidence_atom_count: 0,
    relationship_count: 0,
    trace_summary: { trace_count: 0, atom_count: 0 },
  };
  const pdfSpine = artifact.pdf_spine_summary || {
    accepted_count: 0,
    trace_summary: { trace_count: 0, atom_count: 0 },
  };
  return {
    verdict: artifact.pdf_tei_verdict,
    rationale: artifact.pdf_tei_rationale,
    tei_parser_backend: String(
      artifact.tei_parse_summary?.parser_backend || 'tei_xml',
    ),
    pdf_parser_backend: String(
      artifact.pdf_parse_summary?.parser_backend || 'pdf_local',
    ),
    tei_quality_gate_passed: Boolean(teiSpine.quality_gate_passed),
    dirty_pdf_blocked: Boolean(
      artifact.dirty_pdf_gate_summary?.llm_extraction_blocked,
    ),
    tei_accepted_count: Number(teiSpine.accepted_count || 0),
    tei_trace_count: Number(teiSpine.trace_summary?.trace_count || 0),
    pdf_accepted_count: Number(pdfSpine.accepted_count || 0),
    tei_quoteable_spans: Number(
      artifact.tei_parse_summary?.quoteable_span_count || 0,
    ),
    pdf_quoteable_spans: Number(
      artifact.pdf_parse_summary?.quoteable_span_count || 0,
    ),
  };
}

export function resolvePdfTeiMilestonePreview():
  | (AtlasPdfTeiMilestonePanel & { preview_source: 'run_artifact' })
  | null {
  if (
    atlasPdfTeiMilestoneArtifact.schema_version !== ATLAS_PDF_TEI_MILESTONE_SCHEMA
  ) {
    return null;
  }
  return {
    ...mapPdfTeiArtifactToPanel(atlasPdfTeiMilestoneArtifact),
    preview_source: 'run_artifact',
  };
}

export type AtlasDemoLoopPolishArtifact = {
  schema_version: string;
  status: string;
  packet_id: string;
  demo_loop_verdict: string;
  demo_loop_rationale: string;
  topic: string;
  domain_pack: string;
  mode: string;
  fixture_mode: boolean;
  resolver_summary: {
    resolved_count: number;
    backend_counts: Record<string, number>;
  };
  source_status_counts: Record<string, number>;
  ranked_source_count: number;
  abstract_evidence_summary: {
    accepted_claims_total: number;
    rejected_claims_total: number;
    card_count: number;
  };
  selective_fulltext_summary: {
    acquisition_count: number;
    status_counts: Record<string, number>;
  };
  improvement_recommendation: {
    recommended_packet: string;
    dominant_signal: string;
    rationale: string;
  };
  field_report_summary: {
    cluster_count: number;
    metadata_record_count: number;
  };
  db_spine_summary: {
    status: string;
    accepted_claims_total: number;
  };
  trace_summary: {
    trace_count: number;
    atom_count: number;
  };
};

export type AtlasDemoLoopPolishPanel = {
  verdict: string;
  rationale: string;
  topic: string;
  resolved_count: number;
  ranked_source_count: number;
  accepted_claims_total: number;
  fulltext_acquisition_count: number;
  fulltext_clean_count: number;
  recommended_packet: string;
  dominant_signal: string;
  trace_count: number;
  db_accepted_claims: number;
};

export const atlasDemoLoopPolishArtifact =
  demoLoopPolish as AtlasDemoLoopPolishArtifact;

const ATLAS_DEMO_LOOP_POLISH_SCHEMA = 'atlas_demo_loop_polish_v0.1.0';

export function mapDemoLoopArtifactToPanel(
  artifact: AtlasDemoLoopPolishArtifact,
): AtlasDemoLoopPolishPanel {
  const fulltext = artifact.selective_fulltext_summary || {
    acquisition_count: 0,
    status_counts: {},
  };
  return {
    verdict: artifact.demo_loop_verdict,
    rationale: artifact.demo_loop_rationale,
    topic: artifact.topic,
    resolved_count: Number(artifact.resolver_summary?.resolved_count || 0),
    ranked_source_count: Number(artifact.ranked_source_count || 0),
    accepted_claims_total: Number(
      artifact.abstract_evidence_summary?.accepted_claims_total || 0,
    ),
    fulltext_acquisition_count: Number(fulltext.acquisition_count || 0),
    fulltext_clean_count: Number(
      fulltext.status_counts?.full_text_clean_text_ready || 0,
    ),
    recommended_packet: String(
      artifact.improvement_recommendation?.recommended_packet || 'unknown',
    ),
    dominant_signal: String(
      artifact.improvement_recommendation?.dominant_signal || 'unknown',
    ),
    trace_count: Number(artifact.trace_summary?.trace_count || 0),
    db_accepted_claims: Number(
      artifact.db_spine_summary?.accepted_claims_total || 0,
    ),
  };
}

export function resolveDemoLoopPolishPreview():
  | (AtlasDemoLoopPolishPanel & { preview_source: 'run_artifact' })
  | null {
  if (
    atlasDemoLoopPolishArtifact.schema_version !== ATLAS_DEMO_LOOP_POLISH_SCHEMA
  ) {
    return null;
  }
  return {
    ...mapDemoLoopArtifactToPanel(atlasDemoLoopPolishArtifact),
    preview_source: 'run_artifact',
  };
}

export type AtlasFullAtlasRefreshChecklistArtifact = {
  schema_version: string;
  status: string;
  packet_id: string;
  full_atlas_refresh_verdict: string;
  full_atlas_refresh_rationale: string;
  evidence_quality_verdict: string;
  operator_packet_validation: {
    status: string;
    valid_count: number;
    total_count: number;
    artifacts: Array<{ packet_id: string; status: string; error_count: number }>;
  };
  fixture_refresh_summary?: { status: string; refreshed_packets?: Record<string, string> };
};

export type AtlasFullAtlasRefreshPanel = {
  verdict: string;
  rationale: string;
  evidence_quality_verdict: string;
  valid_packet_count: number;
  total_packet_count: number;
  fixture_refresh_status: string;
};

export const atlasFullAtlasRefreshChecklistArtifact =
  fullAtlasRefreshChecklist as AtlasFullAtlasRefreshChecklistArtifact;

const ATLAS_FULL_ATLAS_REFRESH_SCHEMA = 'atlas_full_atlas_refresh_checklist_v0.1.0';

export function mapFullAtlasRefreshArtifactToPanel(
  artifact: AtlasFullAtlasRefreshChecklistArtifact,
): AtlasFullAtlasRefreshPanel {
  const validation = artifact.operator_packet_validation || {
    valid_count: 0,
    total_count: 0,
  };
  return {
    verdict: artifact.full_atlas_refresh_verdict,
    rationale: artifact.full_atlas_refresh_rationale,
    evidence_quality_verdict: artifact.evidence_quality_verdict,
    valid_packet_count: Number(validation.valid_count || 0),
    total_packet_count: Number(validation.total_count || 0),
    fixture_refresh_status: String(
      artifact.fixture_refresh_summary?.status || 'skipped',
    ),
  };
}

export function resolveFullAtlasRefreshChecklistPreview():
  | (AtlasFullAtlasRefreshPanel & { preview_source: 'run_artifact' })
  | null {
  if (
    atlasFullAtlasRefreshChecklistArtifact.schema_version !==
    ATLAS_FULL_ATLAS_REFRESH_SCHEMA
  ) {
    return null;
  }
  return {
    ...mapFullAtlasRefreshArtifactToPanel(atlasFullAtlasRefreshChecklistArtifact),
    preview_source: 'run_artifact',
  };
}

export type AtlasOpenAISynthesisSpecArtifact = {
  schema_version: string;
  status: string;
  packet_id: string;
  spec_verdict: string;
  spec_rationale: string;
  ticket_059_status: string;
  implementation_blocked: boolean;
  no_paid_api_calls: boolean;
  example_packet_valid: boolean;
  synthesis_readiness: {
    synthesis_readiness_passed: boolean;
    openai_synthesis_blocked: boolean;
  };
};

export type AtlasOpenAISynthesisSpecPanel = {
  verdict: string;
  rationale: string;
  ticket_status: string;
  implementation_blocked: boolean;
  example_packet_valid: boolean;
  synthesis_readiness_passed: boolean;
};

export const atlasOpenAISynthesisAdapterSpecArtifact =
  openaiSynthesisAdapterSpec as AtlasOpenAISynthesisSpecArtifact;

const ATLAS_OPENAI_SYNTHESIS_SPEC_SCHEMA = 'atlas_openai_synthesis_adapter_spec_v0.1.0';

export function mapOpenAISynthesisSpecArtifactToPanel(
  artifact: AtlasOpenAISynthesisSpecArtifact,
): AtlasOpenAISynthesisSpecPanel {
  const readiness = artifact.synthesis_readiness || {
    synthesis_readiness_passed: false,
    openai_synthesis_blocked: true,
  };
  return {
    verdict: artifact.spec_verdict,
    rationale: artifact.spec_rationale,
    ticket_status: artifact.ticket_059_status,
    implementation_blocked: Boolean(artifact.implementation_blocked),
    example_packet_valid: Boolean(artifact.example_packet_valid),
    synthesis_readiness_passed: Boolean(readiness.synthesis_readiness_passed),
  };
}

export function resolveOpenAISynthesisAdapterSpecPreview():
  | (AtlasOpenAISynthesisSpecPanel & { preview_source: 'run_artifact' })
  | null {
  if (
    atlasOpenAISynthesisAdapterSpecArtifact.schema_version !==
    ATLAS_OPENAI_SYNTHESIS_SPEC_SCHEMA
  ) {
    return null;
  }
  return {
    ...mapOpenAISynthesisSpecArtifactToPanel(atlasOpenAISynthesisAdapterSpecArtifact),
    preview_source: 'run_artifact',
  };
}

export type AtlasSynthesisHumanReviewSentence = {
  index: number;
  text: string;
  cited_claim_refs: string[];
  cited_atom_refs: string[];
  cited_source_refs: string[];
  issues: string[];
  min_overlap_count: number;
};

export type AtlasSynthesisHumanReviewItem = {
  output_id: string;
  packet_id: string;
  review_status: string;
  needs_human_review: boolean;
  review_mode?: string;
  governor_verdict?: string;
  auto_signed_off?: boolean;
  automated_review_status?: string;
  provider: string;
  sentence_count: number;
  flagged_sentence_count: number;
  flagged_sentences: AtlasSynthesisHumanReviewSentence[];
  sign_off_status?: 'not_eligible' | 'pending_sign_off' | 'signed_off';
  signed_off_at?: string;
  sign_off_id?: string;
};

export type AtlasSynthesisHumanReviewSignOffSummary = {
  eligible_count: number;
  signed_off_count: number;
  pending_sign_off_count: number;
};

export type AtlasSynthesisCircuitBreakerGuidance = {
  schema_version: string;
  circuit_breaker_status: string;
  reason_opened?: string | null;
  consecutive_synthesis_failures: number;
  consecutive_unsupported_outputs: number;
  opened_at?: string | null;
  latest_ledger_path?: string | null;
  latest_audit_log_path?: string | null;
  reset_instructions: string;
};

export type AtlasSynthesisGovernorSummary = {
  review_mode: string;
  automated_review_verdict: string;
  auto_signed_off_count: number;
  flagged_count: number;
  circuit_breaker_status: string;
  latest_stop_reason?: string | null;
  latest_generated_instruction_packet?: string | null;
  latest_draft_ticket_path?: string | null;
  draft_ticket_status?: string;
  draft_expected_files_backfill_recommended?: boolean;
  expected_files_backfilled_at?: string | null;
  last_patch_revalidation?: {
    status?: string | null;
    validation_verdict?: string | null;
    passed?: boolean | null;
    reason_count?: number | null;
    bundle_path_summary?: string | null;
  } | null;
  instruction_packet_ticket_draft_recommended?: boolean;
  local_implementation_handoff_recommended?: boolean;
  provider_summary: Record<string, number>;
  cost_summary: {
    provider_id?: string | null;
    max_usd_per_run?: number | null;
    max_tokens_per_call?: number | null;
    recorded_cost_usd?: number | string | null;
    no_paid_api_calls?: boolean | null;
  };
  circuit_breaker_guidance?: AtlasSynthesisCircuitBreakerGuidance;
};

export type AtlasReleaseGovernorArtifact = {
  schema_version: string;
  status: string;
  autonomy_tier: {
    configured_tier: number;
    effective_tier: number;
    tier_name: string;
  };
  latest_batch_path?: string | null;
  latest_batch_id?: string | null;
  batch_status: string;
  governor_verdict: string;
  release_governor_dry_run_recommended?: boolean;
  batch_candidate_recommended?: boolean;
  implementation_branch_recommended?: boolean;
  release_push_recommended?: boolean;
  release_merge_recommended?: boolean;
  release_publish_recommended?: boolean;
  circuit_breaker_status: string;
  latest_draft_ticket_path?: string | null;
  next_release_action?: string | null;
  autonomy_tier_required_for_next_action?: number | null;
  batch_assembly_block_reasons?: string[];
  failure_reasons: string[];
  forbidden_actions: string[];
  operator_commands: Record<string, string>;
  updated_at?: string | null;
};

export type AtlasReleaseGovernorPanel = AtlasReleaseGovernorArtifact;

export type AtlasTier2PatchStagingArtifact = {
  schema_version: string;
  status: string;
  bundle_schema_version: string;
  bundle_id?: string | null;
  draft_ticket_label?: string | null;
  draft_ticket_path_summary?: string | null;
  instruction_packet_label?: string | null;
  instruction_packet_path_summary?: string | null;
  branch_name?: string | null;
  validation_verdict: string;
  risk_class: string;
  changed_file_count: number;
  lines_added: number;
  lines_removed: number;
  safety_audit_required: boolean;
  test_plan_count: number;
  validation_reasons: string[];
  next_recommended_action: string;
  apply_ready?: boolean;
  stop_state?: boolean;
  preview_freshness: string;
  patch_revalidation_summary?: {
    status?: string | null;
    validation_verdict?: string | null;
    passed?: boolean | null;
    reason_count?: number | null;
    bundle_path_summary?: string | null;
    backfilled_at?: string | null;
  } | null;
  source_bundle_path?: string | null;
  generated_at?: string | null;
  updated_at?: string | null;
  forbidden_in_preview?: string[];
};

export type AtlasTier2PatchStagingPanel = AtlasTier2PatchStagingArtifact;

export type AtlasSynthesisHumanReviewArtifact = {
  schema_version: string;
  status: string;
  packet_id: string;
  review_summary: {
    total_outputs: number;
    needs_human_review_count: number;
    grounding_passed_count: number;
  };
  sign_off_summary?: AtlasSynthesisHumanReviewSignOffSummary;
  governor_summary?: AtlasSynthesisGovernorSummary;
  circuit_breaker_guidance?: AtlasSynthesisCircuitBreakerGuidance;
  review_queue: AtlasSynthesisHumanReviewItem[];
  flagged_review_queue: AtlasSynthesisHumanReviewItem[];
  operator_actions: string[];
};

export type AtlasSynthesisHumanReviewPanel = {
  total_outputs: number;
  needs_human_review_count: number;
  grounding_passed_count: number;
  flagged_items: AtlasSynthesisHumanReviewItem[];
  operator_actions: string[];
  sign_off_summary: AtlasSynthesisHumanReviewSignOffSummary;
  governor_summary: AtlasSynthesisGovernorSummary;
  circuit_breaker_guidance: AtlasSynthesisCircuitBreakerGuidance;
  pending_sign_offs: AtlasSynthesisHumanReviewItem[];
  signed_off_outputs: AtlasSynthesisHumanReviewItem[];
};

export type AtlasSynthesisHumanReviewAlert = {
  output_id: string;
  packet_id: string;
  provider: string;
  review_status: string;
  flagged_sentence_count: number;
  sentence_preview: string;
  primary_issue: string;
};

export type AtlasSynthesisHumanReviewAlertsPanel = {
  alert_count: number;
  flagged_output_count: number;
  headline: string;
  summary: string;
  alerts: AtlasSynthesisHumanReviewAlert[];
  operator_actions: string[];
  anchor_id: string;
};

const SYNTHESIS_HUMAN_REVIEW_ANCHOR_ID = 'synthesis-human-review';

function truncateAlertText(value: string, maxLength = 140): string {
  const trimmed = value.trim();
  if (trimmed.length <= maxLength) {
    return trimmed;
  }
  return `${trimmed.slice(0, maxLength - 1).trim()}…`;
}

export function buildSynthesisHumanReviewFlaggedAlerts(
  panel: AtlasSynthesisHumanReviewPanel,
): AtlasSynthesisHumanReviewAlertsPanel | null {
  if (!panel.flagged_items.length) {
    return null;
  }
  const alerts: AtlasSynthesisHumanReviewAlert[] = panel.flagged_items.map((item) => {
    const firstSentence = item.flagged_sentences[0];
    const primaryIssue =
      firstSentence?.issues?.find(Boolean) ||
      'Grounding check flagged this synthesis output for human review.';
    return {
      output_id: item.output_id,
      packet_id: item.packet_id,
      provider: item.provider,
      review_status: item.review_status,
      flagged_sentence_count: item.flagged_sentence_count,
      sentence_preview: truncateAlertText(firstSentence?.text || ''),
      primary_issue: truncateAlertText(primaryIssue, 180),
    };
  });
  const flaggedOutputCount = panel.flagged_items.length;
  const alertCount = alerts.reduce(
    (total, item) => total + Math.max(item.flagged_sentence_count, 1),
    0,
  );
  return {
    alert_count: alertCount,
    flagged_output_count: flaggedOutputCount,
    headline:
      flaggedOutputCount === 1
        ? '1 synthesis output needs human review'
        : `${flaggedOutputCount} synthesis outputs need human review`,
    summary: `${panel.needs_human_review_count} of ${panel.total_outputs} scanned outputs flagged after deterministic grounding checks.`,
    alerts,
    operator_actions: panel.operator_actions,
    anchor_id: SYNTHESIS_HUMAN_REVIEW_ANCHOR_ID,
  };
}

export function resolveSynthesisHumanReviewFlaggedAlerts():
  | (AtlasSynthesisHumanReviewAlertsPanel & { preview_source: 'run_artifact' })
  | null {
  const preview = resolveSynthesisHumanReviewPreview();
  if (!preview) {
    return null;
  }
  const alerts = buildSynthesisHumanReviewFlaggedAlerts(preview);
  if (!alerts) {
    return null;
  }
  return {
    ...alerts,
    preview_source: 'run_artifact',
  };
}

export const atlasSynthesisHumanReviewArtifact =
  synthesisHumanReview as AtlasSynthesisHumanReviewArtifact;

export const atlasReleaseGovernorArtifact =
  releaseGovernor as AtlasReleaseGovernorArtifact;

const ATLAS_RELEASE_GOVERNOR_SCHEMA = 'atlas_release_governor_v0.1.0';

export function resolveReleaseGovernorPreview():
  | (AtlasReleaseGovernorPanel & { preview_source: 'run_artifact' })
  | null {
  if (atlasReleaseGovernorArtifact.schema_version !== ATLAS_RELEASE_GOVERNOR_SCHEMA) {
    return null;
  }
  return {
    ...atlasReleaseGovernorArtifact,
    preview_source: 'run_artifact',
  };
}

const ATLAS_TIER2_PATCH_STAGING_SCHEMA = 'atlas_tier2_patch_staging_v0.1.0';

export const atlasTier2PatchStagingArtifact =
  tier2PatchStaging as AtlasTier2PatchStagingArtifact;

export function resolveTier2PatchStagingPreview():
  | (AtlasTier2PatchStagingPanel & { preview_source: 'run_artifact' })
  | null {
  if (atlasTier2PatchStagingArtifact.schema_version !== ATLAS_TIER2_PATCH_STAGING_SCHEMA) {
    return null;
  }
  return {
    ...atlasTier2PatchStagingArtifact,
    preview_source: 'run_artifact',
  };
}

const ATLAS_SYNTHESIS_HUMAN_REVIEW_SCHEMA = 'atlas_synthesis_human_review_v0.1.0';

export function mapSynthesisHumanReviewArtifactToPanel(
  artifact: AtlasSynthesisHumanReviewArtifact,
): AtlasSynthesisHumanReviewPanel {
  const summary = artifact.review_summary || {
    total_outputs: 0,
    needs_human_review_count: 0,
    grounding_passed_count: 0,
  };
  const signOffSummary = artifact.sign_off_summary || {
    eligible_count: 0,
    signed_off_count: 0,
    pending_sign_off_count: 0,
  };
  const governorSummary = artifact.governor_summary || {
    review_mode: 'automated',
    automated_review_verdict: 'UNKNOWN',
    auto_signed_off_count: 0,
    flagged_count: 0,
    circuit_breaker_status: 'closed',
    latest_stop_reason: null,
    latest_generated_instruction_packet: null,
    latest_draft_ticket_path: null,
    draft_ticket_status: 'missing',
    draft_expected_files_backfill_recommended: false,
    expected_files_backfilled_at: null,
    last_patch_revalidation: null,
    instruction_packet_ticket_draft_recommended: false,
    local_implementation_handoff_recommended: false,
    provider_summary: {},
    cost_summary: {},
  };
  const circuitGuidance = artifact.circuit_breaker_guidance ||
    governorSummary.circuit_breaker_guidance || {
      schema_version: 'autonomous_synthesis_governor_v0.1.0',
      circuit_breaker_status: governorSummary.circuit_breaker_status || 'closed',
      reason_opened: governorSummary.latest_stop_reason || null,
      consecutive_synthesis_failures: 0,
      consecutive_unsupported_outputs: 0,
      reset_instructions:
        'Inspect circuit breaker status via the autonomous synthesis governor operator CLI.',
    };
  const reviewQueue = Array.isArray(artifact.review_queue) ? artifact.review_queue : [];
  return {
    total_outputs: Number(summary.total_outputs || 0),
    needs_human_review_count: Number(summary.needs_human_review_count || 0),
    grounding_passed_count: Number(summary.grounding_passed_count || 0),
    flagged_items: Array.isArray(artifact.flagged_review_queue)
      ? artifact.flagged_review_queue
      : [],
    operator_actions: Array.isArray(artifact.operator_actions)
      ? artifact.operator_actions.filter(Boolean)
      : [],
    sign_off_summary: {
      eligible_count: Number(signOffSummary.eligible_count || 0),
      signed_off_count: Number(signOffSummary.signed_off_count || 0),
      pending_sign_off_count: Number(signOffSummary.pending_sign_off_count || 0),
    },
    governor_summary: {
      review_mode: governorSummary.review_mode || 'automated',
      automated_review_verdict: governorSummary.automated_review_verdict || 'UNKNOWN',
      auto_signed_off_count: Number(governorSummary.auto_signed_off_count || 0),
      flagged_count: Number(governorSummary.flagged_count || 0),
      circuit_breaker_status: governorSummary.circuit_breaker_status || 'closed',
      latest_stop_reason: governorSummary.latest_stop_reason || null,
      latest_generated_instruction_packet:
        governorSummary.latest_generated_instruction_packet || null,
      latest_draft_ticket_path: governorSummary.latest_draft_ticket_path || null,
      draft_ticket_status: governorSummary.draft_ticket_status || 'missing',
      instruction_packet_ticket_draft_recommended: Boolean(
        governorSummary.instruction_packet_ticket_draft_recommended,
      ),
      local_implementation_handoff_recommended: Boolean(
        governorSummary.local_implementation_handoff_recommended,
      ),
      provider_summary: governorSummary.provider_summary || {},
      cost_summary: governorSummary.cost_summary || {},
      circuit_breaker_guidance: circuitGuidance,
    },
    circuit_breaker_guidance: {
      schema_version: circuitGuidance.schema_version || 'autonomous_synthesis_governor_v0.1.0',
      circuit_breaker_status: circuitGuidance.circuit_breaker_status || 'closed',
      reason_opened: circuitGuidance.reason_opened || null,
      consecutive_synthesis_failures: Number(
        circuitGuidance.consecutive_synthesis_failures || 0,
      ),
      consecutive_unsupported_outputs: Number(
        circuitGuidance.consecutive_unsupported_outputs || 0,
      ),
      opened_at: circuitGuidance.opened_at || null,
      latest_ledger_path: circuitGuidance.latest_ledger_path || null,
      latest_audit_log_path: circuitGuidance.latest_audit_log_path || null,
      reset_instructions: circuitGuidance.reset_instructions || '',
    },
    pending_sign_offs: reviewQueue.filter(
      (row) => row.sign_off_status === 'pending_sign_off',
    ),
    signed_off_outputs: reviewQueue.filter((row) => row.sign_off_status === 'signed_off'),
  };
}

export function resolveSynthesisHumanReviewPreview():
  | (AtlasSynthesisHumanReviewPanel & { preview_source: 'run_artifact' })
  | null {
  if (
    atlasSynthesisHumanReviewArtifact.schema_version !==
    ATLAS_SYNTHESIS_HUMAN_REVIEW_SCHEMA
  ) {
    return null;
  }
  return {
    ...mapSynthesisHumanReviewArtifactToPanel(atlasSynthesisHumanReviewArtifact),
    preview_source: 'run_artifact',
  };
}

function formatNextRecommendedPacket(
  value: string | { id: string; title: string } | undefined,
  fallback: string,
): string {
  if (!value) {
    return fallback;
  }
  if (typeof value === 'string') {
    return value;
  }
  return value.title || value.id || fallback;
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
    next_recommended_packet: formatNextRecommendedPacket(
      artifact.next_recommended_packet,
      'source-health-persistence',
    ),
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
    next_recommended_packet: formatNextRecommendedPacket(
      artifact.next_recommended_packet,
      'graph-connection-metrics',
    ),
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

export function tier2PatchFreshnessBadgeColor(freshness: string): string {
  const normalized = freshness.trim().toLowerCase();
  if (normalized === 'fresh') {
    return '#3d8f6a';
  }
  if (normalized === 'stale') {
    return '#c9a227';
  }
  if (normalized === 'missing') {
    return '#b85c5c';
  }
  return '#5c6b8a';
}

export function tier2PatchFreshnessBadgeLabel(freshness: string): string {
  const normalized = freshness.trim().toLowerCase();
  if (normalized === 'fresh') {
    return 'Atlas preview fresh';
  }
  if (normalized === 'stale') {
    return 'Atlas preview stale — refresh recommended';
  }
  if (normalized === 'missing') {
    return 'Atlas preview missing — refresh required';
  }
  return `Atlas preview ${humanizeLabel(freshness)}`;
}

export function tier2PatchValidationVerdictBadgeColor(verdict: string): string {
  const normalized = verdict.trim().toUpperCase();
  if (normalized === 'GO') {
    return '#3d8f6a';
  }
  if (normalized === 'PARTIAL') {
    return '#c9a227';
  }
  if (normalized === 'NO-GO') {
    return '#b85c5c';
  }
  if (normalized === 'PENDING') {
    return '#5c6b8a';
  }
  return '#5c6b8a';
}

export function tier2PatchValidationVerdictBadgeLabel(verdict: string): string {
  const normalized = verdict.trim().toUpperCase();
  if (normalized === 'GO') {
    return 'Patch validation GO';
  }
  if (normalized === 'PARTIAL') {
    return 'Patch validation PARTIAL — review before apply';
  }
  if (normalized === 'NO-GO') {
    return 'Patch validation NO-GO — fix before apply';
  }
  if (normalized === 'PENDING') {
    return 'Patch validation pending';
  }
  return `Patch validation ${humanizeLabel(verdict)}`;
}

export function formatEdgeSummary(edge: AtlasPreviewEdge): string {
  const scope = edge.scope ? ` (${edge.scope})` : '';
  return `${edge.source_label} ${humanizeLabel(edge.predicate)} ${edge.target_label}${scope}`;
}

export { formatPublicTimestamp, humanizeLabel };
