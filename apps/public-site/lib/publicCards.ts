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
