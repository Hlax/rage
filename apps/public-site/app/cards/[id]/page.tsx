// Read-only card detail page. Static JSON only; no fetches or API routes.

import Link from 'next/link';
import { notFound } from 'next/navigation';

import {
  conceptToSlug,
  findCardById,
  publicCards,
} from '../../../lib/publicCards';

type PageProps = {
  params: Promise<{ id: string }>;
};

export function generateStaticParams() {
  return publicCards.map((card) => ({ id: card.id }));
}

function RelatedCardLink({ cardId }: { cardId: string }) {
  const related = findCardById(cardId);
  if (!related) {
    return <span>{cardId}</span>;
  }
  return (
    <Link href={`/cards/${related.id}`} style={{ color: '#9eb4ff' }}>
      {related.title}
    </Link>
  );
}

export default async function CardDetailPage({ params }: PageProps) {
  const { id } = await params;
  const card = findCardById(id);
  if (!card) {
    notFound();
  }

  return (
    <main style={{ maxWidth: 760, margin: '0 auto', padding: '3rem 1.5rem' }}>
      <p style={{ margin: 0, fontSize: '0.8rem', color: '#8b93a3' }}>
        <Link href="/" style={{ color: '#9eb4ff' }}>
          Public cards
        </Link>
        {' · card detail'}
      </p>
      <h1 style={{ fontSize: '1.6rem', lineHeight: 1.25, marginTop: '1rem' }}>
        {card.title}
      </h1>
      <p style={{ margin: '0.5rem 0 0', fontSize: '0.85rem', color: '#8b93a3' }}>
        {card.type} · confidence: {card.confidence} · sources: {card.source_count} ·{' '}
        {card.public_detail_level}
      </p>
      <p style={{ color: '#aeb4c0', lineHeight: 1.65, marginTop: '1.5rem' }}>
        {card.summary}
      </p>

      <section style={{ marginTop: '2rem' }}>
        <h2 style={{ fontSize: '1rem' }}>Concepts</h2>
        <ul style={{ paddingLeft: '1.2rem', color: '#aeb4c0' }}>
          {card.concepts.map((concept) => (
            <li key={concept}>
              <Link
                href={`/concepts/${conceptToSlug(concept)}`}
                style={{ color: '#9eb4ff' }}
              >
                {concept}
              </Link>
            </li>
          ))}
        </ul>
      </section>

      {card.public_caveats && card.public_caveats.length > 0 ? (
        <section style={{ marginTop: '2rem' }}>
          <h2 style={{ fontSize: '1rem' }}>Caveats</h2>
          <ul style={{ paddingLeft: '1.2rem', color: '#aeb4c0' }}>
            {card.public_caveats.map((caveat) => (
              <li key={caveat}>{caveat}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {card.public_source_metadata && card.public_source_metadata.length > 0 ? (
        <section style={{ marginTop: '2rem' }}>
          <h2 style={{ fontSize: '1rem' }}>Public source metadata</h2>
          <ul style={{ listStyle: 'none', padding: 0, color: '#aeb4c0' }}>
            {card.public_source_metadata.map((source) => (
              <li key={source.title} style={{ marginBottom: '0.5rem' }}>
                {source.title}
                {source.year ? ` (${source.year})` : ''}
                {source.source_type ? ` · ${source.source_type}` : ''}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {card.related_cards && card.related_cards.length > 0 ? (
        <section style={{ marginTop: '2rem' }}>
          <h2 style={{ fontSize: '1rem' }}>Related cards</h2>
          <ul style={{ paddingLeft: '1.2rem', color: '#aeb4c0' }}>
            {card.related_cards.map((relatedId) => (
              <li key={relatedId}>
                <RelatedCardLink cardId={relatedId} />
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <footer
        style={{
          marginTop: '3rem',
          paddingTop: '1rem',
          borderTop: '1px solid #2a2f3a',
          fontSize: '0.8rem',
          color: '#8b93a3',
        }}
      >
        <p style={{ margin: 0 }}>Card ID: {card.id}</p>
        <p style={{ margin: '0.25rem 0 0' }}>Last updated: {card.updated_at}</p>
      </footer>
    </main>
  );
}
