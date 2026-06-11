import type { ReactNode } from 'react';

export const metadata = {
  title: 'Research Graph Engine — Public Cards',
  description:
    'Read-only public export surface for the Research Graph Engine. Renders static JSON snapshots only.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body
        style={{
          fontFamily:
            'ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif',
          margin: 0,
          background: '#0f1115',
          color: '#e6e8ec',
          minHeight: '100vh',
        }}
      >
        {children}
      </body>
    </html>
  );
}
