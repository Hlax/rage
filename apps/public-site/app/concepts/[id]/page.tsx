// Read-only concept detail page. Concept routes use URL slugs derived from labels.

import Link from 'next/link';
import { notFound } from 'next/navigation';

import {
  cardsForConcept,
  conceptToSlug,
  findConceptBySlug,
  listConceptSlugs,
} from '../../../lib/publicCards';

type PageProps = {
  params: Promise<{ id: string }>;
};

export function generateStaticParams() {
  return listConceptSlugs().map((id) => ({ id }));
}

export default async function ConceptDetailPage({ params }: PageProps) {
  const { id } = await params;
  const conceptLabel = findConceptBySlug(id);
  if (!conceptLabel) {
    notFound();
  }

  const matchingCards = cardsForConcept(conceptLabel);

  return (
    <main style={{ maxWidth: 760, margin: '0 auto', padding: '3rem 1.5rem' }}>
      <p style={{ margin: 0, fontSize: '0.8rem', color: '#8b93a3' }}>
        <Link href="/" style={{ color: '#9eb4ff' }}>
          Public cards
        </Link>
        {' · concept detail'}
      </p>
      <h1 style={{ fontSize: '1.6rem', lineHeight: 1.25, marginTop: '1rem' }}>
        {conceptLabel}
      </h1>
      <p style={{ color: '#aeb4c0', lineHeight: 1.6, marginTop: '0.75rem' }}>
        Public cards referencing this concept from the static export snapshot.
      </p>

      <section style={{ marginTop: '2rem' }}>
        <h2 style={{ fontSize: '1rem' }}>
          Cards ({matchingCards.length})
        </h2>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {matchingCards.map((card) => (
            <li
              key={card.id}
              style={{
                border: '1px solid #2a2f3a',
                borderRadius: 8,
                padding: '1rem 1.25rem',
                marginBottom: '1rem',
                background: '#161922',
              }}
            >
              <p style={{ margin: 0, fontSize: '0.75rem', color: '#8b93a3' }}>
                {card.type} · confidence: {card.confidence}
              </p>
              <h3 style={{ margin: '0.35rem 0', fontSize: '1rem' }}>
                <Link href={`/cards/${card.id}`} style={{ color: '#e6e8ec' }}>
                  {card.title}
                </Link>
              </h3>
              <p style={{ margin: 0, color: '#aeb4c0', lineHeight: 1.55 }}>
                {card.summary}
              </p>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
