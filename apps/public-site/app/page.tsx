// Read-only public list page.
// Data comes from static JSON imports only (apps/public-site/public/data/).
// No fetches, no API routes, no forms, no raw HTML rendering.

import Link from 'next/link';

import memos from '../public/data/public_memos.json';
import buildInfo from '../public/data/build_info.json';
import {
  conceptToSlug,
  formatPublicTimestamp,
  formatSourceCount,
  humanizeLabel,
  publicCards,
} from '../lib/publicCards';

export default function HomePage() {
  const cardList = publicCards;
  return (
    <main style={{ maxWidth: 760, margin: '0 auto', padding: '3rem 1.5rem' }}>
      <p
        style={{
          fontSize: '0.8rem',
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: '#8b93a3',
        }}
      >
        Read-only public export surface
      </p>
      <h1 style={{ fontSize: '1.8rem', lineHeight: 1.25 }}>
        Research Graph Engine
      </h1>
      <p style={{ color: '#aeb4c0', lineHeight: 1.6 }}>
        This site renders public-safe research cards exported as static JSON
        snapshots from a local-first research engine. It has no write routes,
        no source ingestion, and no agent execution. It never connects to the
        private local engine.{' '}
        <Link href="/about" style={{ color: '#9eb4ff' }}>
          How this works
        </Link>
        .
      </p>

      <section style={{ marginTop: '2.5rem' }}>
        <h2 style={{ fontSize: '1.1rem' }}>
          Public cards ({cardList.length})
        </h2>
        {cardList.length === 0 ? (
          <div
            style={{
              border: '1px dashed #2a2f3a',
              borderRadius: 8,
              padding: '1.5rem 1.25rem',
              background: '#161922',
              color: '#aeb4c0',
              lineHeight: 1.6,
            }}
          >
            <p style={{ margin: 0 }}>No public cards in this snapshot yet.</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '0.85rem' }}>
              Cards appear here only after a research run passes deterministic
              validation and the public export safety audit.
            </p>
          </div>
        ) : null}
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {cardList.map((card) => (
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
                {humanizeLabel(card.type)} · {humanizeLabel(card.confidence)}{' '}
                confidence · {formatSourceCount(card.source_count)}
              </p>
              <h3 style={{ margin: '0.35rem 0', fontSize: '1rem' }}>
                <Link href={`/cards/${card.id}`} style={{ color: '#e6e8ec' }}>
                  {card.title}
                </Link>
              </h3>
              <p style={{ margin: 0, color: '#aeb4c0', lineHeight: 1.55 }}>
                {card.summary}
              </p>
              {card.concepts.length > 0 ? (
                <p
                  style={{
                    margin: '0.75rem 0 0',
                    fontSize: '0.8rem',
                    color: '#8b93a3',
                  }}
                >
                  Concepts:{' '}
                  {card.concepts.map((concept, index) => (
                    <span key={concept}>
                      {index > 0 ? ', ' : ''}
                      <Link
                        href={`/concepts/${conceptToSlug(concept)}`}
                        style={{ color: '#9eb4ff' }}
                      >
                        {concept}
                      </Link>
                    </span>
                  ))}
                </p>
              ) : null}
            </li>
          ))}
        </ul>
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
          Export schema {String(buildInfo.export_schema_version)} · phase{' '}
          {String(buildInfo.phase)} · memos: {(memos as unknown[]).length} ·{' '}
          <Link href="/about" style={{ color: '#9eb4ff' }}>
            About
          </Link>
        </p>
        <p style={{ margin: '0.25rem 0 0' }}>
          Last updated: {formatPublicTimestamp(String(buildInfo.generated_at))}
        </p>
      </footer>
    </main>
  );
}
