// Read-only static about page. Hand-written copy only; no dynamic data
// beyond the already-public build info. No fetches, no API routes, no forms.

import Link from 'next/link';

import buildInfo from '../../public/data/build_info.json';
import { formatPublicTimestamp } from '../../lib/publicCards';

export const metadata = {
  title: 'About — Research Graph Engine',
  description:
    'How the Research Graph Engine produces public research cards, what confidence means, and the read-only safety boundary of this site.',
};

const sectionStyle = { marginTop: '2rem' } as const;
const headingStyle = { fontSize: '1.05rem' } as const;
const bodyStyle = { color: '#aeb4c0', lineHeight: 1.65 } as const;
const listStyle = {
  paddingLeft: '1.2rem',
  color: '#aeb4c0',
  lineHeight: 1.65,
} as const;

export default function AboutPage() {
  return (
    <main style={{ maxWidth: 760, margin: '0 auto', padding: '3rem 1.5rem' }}>
      <p style={{ margin: 0, fontSize: '0.8rem', color: '#8b93a3' }}>
        <Link href="/" style={{ color: '#9eb4ff' }}>
          Public cards
        </Link>
        {' · about'}
      </p>
      <h1 style={{ fontSize: '1.6rem', lineHeight: 1.25, marginTop: '1rem' }}>
        About this site
      </h1>
      <p style={bodyStyle}>
        This site is the read-only public surface of the Research Graph
        Engine, a local-first system that turns source documents into scoped
        research claims, concept links, evidence relationships, and the public
        research cards shown here.
      </p>

      <section style={sectionStyle}>
        <h2 style={headingStyle}>How cards are produced</h2>
        <p style={bodyStyle}>
          The engine ingests sources, extracts candidate claims, links them to
          concepts, builds evidence relationships, and detects contradictions.
          A language model only proposes candidates; deterministic Python
          validation decides what is accepted. Nothing a model writes reaches
          the accepted research graph, or this site, without passing schema
          checks, quote-span checks, scope checks, and a full safety audit.
        </p>
      </section>

      <section style={sectionStyle}>
        <h2 style={headingStyle}>Where this data comes from</h2>
        <p style={bodyStyle}>
          The current snapshot is generated from deterministic fixture runs: a
          fixed set of test sources processed by the full pipeline in mock
          model mode. That is why cards carry caveats such as
          &ldquo;fixture-derived synthesis&rdquo; — they demonstrate the
          pipeline end to end, not the conclusions of a live literature
          review. Source metadata on each card is labeled accordingly.
        </p>
      </section>

      <section style={sectionStyle}>
        <h2 style={headingStyle}>What confidence means</h2>
        <p style={bodyStyle}>
          Each card shows a confidence level derived from deterministic
          scoring of the accepted claims behind it:
        </p>
        <ul style={listStyle}>
          <li>
            <strong>Low</strong> — limited or conflicting accepted evidence.
          </li>
          <li>
            <strong>Medium</strong> — consistent accepted evidence with
            meaningful caveats, such as narrow task scope or few sources.
          </li>
          <li>
            <strong>High</strong> — convergent accepted evidence across
            multiple sources with no unresolved contradictions.
          </li>
        </ul>
        <p style={bodyStyle}>
          Confidence is never set by a model directly; it is computed by the
          engine&rsquo;s scoring rules and re-evaluated as evidence changes.
        </p>
      </section>

      <section style={sectionStyle}>
        <h2 style={headingStyle}>Read-only safety boundary</h2>
        <p style={bodyStyle}>
          This site is a static export. It has no write routes, no source
          ingestion routes, and no agent execution routes. It performs no
          network requests to the research engine and cannot reach it: pages
          are pre-rendered from static JSON snapshots at build time. Every
          export passes a fail-closed safety audit before it can be published.
        </p>
      </section>

      <section style={sectionStyle}>
        <h2 style={headingStyle}>Public vs. private data</h2>
        <p style={bodyStyle}>
          Only a curated whitelist of fields is ever exported: card titles,
          summaries, confidence levels, concepts, public caveats, public
          source metadata, related cards, and safe timestamps. The private
          side of the engine — raw source text, prompts, internal
          identifiers, file locations, draft claims, and internal review
          notes — is excluded by policy and checked by deterministic audits
          on every export.
        </p>
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
          {String(buildInfo.phase)}
        </p>
        <p style={{ margin: '0.25rem 0 0' }}>
          Snapshot generated: {formatPublicTimestamp(String(buildInfo.generated_at))}
        </p>
      </footer>
    </main>
  );
}
