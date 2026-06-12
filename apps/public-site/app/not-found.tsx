// Custom 404 in the site's visual language. Static, read-only, no data access.

import Link from 'next/link';

export default function NotFound() {
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
      <h1 style={{ fontSize: '1.8rem', lineHeight: 1.25 }}>Page not found</h1>
      <p style={{ color: '#aeb4c0', lineHeight: 1.6 }}>
        This page is not part of the current public snapshot. Cards and
        concepts appear here only after they pass the engine&rsquo;s
        validation and public export safety audit.
      </p>
      <p style={{ marginTop: '2rem' }}>
        <Link href="/" style={{ color: '#9eb4ff' }}>
          Back to public cards
        </Link>
      </p>
    </main>
  );
}
