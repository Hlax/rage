import snapshot from '../public/data/atlas_snapshot_preview.json';
import coherence from '../public/data/atlas_coherence_preview.json';

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
};

export type AtlasCoherencePreview = {
  schema_version: string;
  overall_coherence_verdict: string;
  population: Record<string, number>;
  preview_label: string;
};

export const atlasSnapshot = snapshot as AtlasPreviewSnapshot;
export const atlasCoherence = coherence as AtlasCoherencePreview;

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
