'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const TABS = [
  { label: 'Plan Trip', href: '/' },
  { label: 'Ingest Reel', href: '/ingest' },
] as const;

export default function NavBar() {
  const pathname = usePathname();
  return (
    <nav className="absolute top-4 left-1/2 -translate-x-1/2 z-20 flex rounded-xl
                    bg-slate-900/80 backdrop-blur-md border border-slate-700/60 p-1 shadow-xl">
      {TABS.map(({ label, href }) => {
        const active = pathname === href;
        return (
          <Link
            key={href}
            href={href}
            className={`px-5 py-1.5 rounded-lg text-sm font-semibold transition-all ${
              active
                ? 'bg-emerald-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
