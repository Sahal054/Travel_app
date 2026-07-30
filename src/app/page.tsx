'use client';

import dynamic from 'next/dynamic';

const MapCanvas = dynamic(() => import('@/components/MapCanvas'), {
  ssr: false,
  loading: () => <div className="w-full h-screen bg-slate-900" />,
});

export default function Home() {
  return <MapCanvas />;
}
