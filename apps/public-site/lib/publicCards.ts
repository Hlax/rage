import cards from '../public/data/public_cards.json';

export type PublicCard = {
  id: string;
  type: string;
  title: string;
  summary: string;
  confidence: string;
  concepts: string[];
  source_count: number;
  public_caveats?: string[];
  public_source_metadata?: Array<{
    title: string;
    year?: number;
    source_type?: string;
  }>;
  related_cards?: string[];
  public_detail_level: string;
  evidence_type?: string;
  public_run_timestamp?: string;
  updated_at: string;
};

export const publicCards = cards as PublicCard[];

const MONTH_NAMES = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
] as const;

/**
 * Presentation-only label formatting for already-exported enum values
 * (e.g. "cluster_card" -> "Cluster card"). Never changes underlying data.
 */
export function humanizeLabel(value: string): string {
  const cleaned = value.replace(/_/g, ' ').trim();
  if (!cleaned) {
    return value;
  }
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
}

/**
 * Deterministic human-readable formatting for safe public ISO timestamps
 * (e.g. "2026-06-12T00:00:00Z" -> "June 12, 2026 (00:00 UTC)").
 * Falls back to the raw value if the shape is unexpected.
 */
export function formatPublicTimestamp(iso: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(iso);
  if (!match) {
    return iso;
  }
  const [, year, month, day, hour, minute] = match;
  const monthName = MONTH_NAMES[Number(month) - 1];
  if (!monthName) {
    return iso;
  }
  return `${monthName} ${Number(day)}, ${year} (${hour}:${minute} UTC)`;
}

export function formatSourceCount(count: number): string {
  return count === 1 ? '1 source' : `${count} sources`;
}

export function conceptToSlug(label: string): string {
  return label
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

export function findConceptBySlug(slug: string): string | undefined {
  for (const card of publicCards) {
    for (const concept of card.concepts) {
      if (conceptToSlug(concept) === slug) {
        return concept;
      }
    }
  }
  return undefined;
}

export function listConceptSlugs(): string[] {
  const slugs = new Set<string>();
  for (const card of publicCards) {
    for (const concept of card.concepts) {
      slugs.add(conceptToSlug(concept));
    }
  }
  return [...slugs].sort();
}

export function cardsForConcept(conceptLabel: string): PublicCard[] {
  return publicCards.filter((card) => card.concepts.includes(conceptLabel));
}

export function findCardById(cardId: string): PublicCard | undefined {
  return publicCards.find((card) => card.id === cardId);
}
