/**
 * Public read-only site: static export only.
 * No server runtime, no API routes, no connection to the private local
 * engine, FastAPI, or SQLite. Data comes from static JSON in public/data/.
 */
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  // Pin tracing to this app so stray lockfiles outside the repo cannot
  // change build behavior.
  outputFileTracingRoot: __dirname,
};

module.exports = nextConfig;
