'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSession, signOut } from 'next-auth/react';
import { useState } from 'react';
import AuthModal from './AuthModal';

const TABS = [
  { label: 'Plan Trip',   href: '/',          icon: '\U0001f5fa\ufe0f' },
  { label: 'Ingest Reel', href: '/ingest',    icon: '\U0001f4f2' },
  { label: 'Itinerary',   href: '/itinerary', icon: '\u2728' },
] as const;

export default function NavBar() {
  const pathname = usePathname();
  const { data: session } = useSession();
  const [showAuth, setShowAuth] = useState(false);

  return (
    <>
      <nav className="fixed top-4 left-1/2 -translate-x-1/2 z-30 flex items-center gap-1
                      rounded-2xl bg-slate-950/90 backdrop-blur-xl border border-slate-700/50 p-1.5 shadow-2xl shadow-black/50">
        {TABS.map(({ label, href, icon }) => {
          const active = pathname === href;
          return (
            <Link key={href} href={href}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
                active
                  ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-md shadow-violet-900/40'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <span className="text-base leading-none">{icon}</span>
              {label}
            </Link>
          );
        })}

        <div className="w-px h-5 bg-slate-700 mx-1" />

        {session ? (
          <button onClick={() => signOut()}
            title={`Signed in as ${session.user?.name ?? session.user?.email}`}
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-xs text-slate-400 hover:text-white transition-colors hover:bg-slate-800/60"
          >
            <span className="h-6 w-6 rounded-full bg-violet-600 flex items-center justify-center text-white text-[10px] font-bold shrink-0">
              {(session.user?.name ?? session.user?.email ?? 'U')[0].toUpperCase()}
            </span>
            <span className="hidden sm:block">Sign out</span>
          </button>
        ) : (
          <button onClick={() => setShowAuth(true)}
            className="px-4 py-2 rounded-xl text-sm font-semibold text-white
                       bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-slate-600 transition-all"
          >
            Sign in
          </button>
        )}
      </nav>

      {showAuth && <AuthModal onClose={() => setShowAuth(false)} />}
    </>
  );
}
