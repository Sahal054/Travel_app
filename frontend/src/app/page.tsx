'use client';

import { Suspense } from 'react';
import dynamic from 'next/dynamic';
import { useSearchParams } from 'next/navigation';

const MapCanvas = dynamic(() => import('@/components/MapCanvas'), {
  ssr: false,
  loading: () => <div className="w-full h-screen bg-slate-950" />,
});

function HomeContent() {
  const params     = useSearchParams();
  const destLat    = params.get('dest_lat');
  const destLng    = params.get('dest_lng');
  const destName   = params.get('dest_name');

  return (
    <MapCanvas
      initialDestLat={destLat  ? parseFloat(destLat)  : undefined}
      initialDestLng={destLng  ? parseFloat(destLng)  : undefined}
      initialDestName={destName ?? undefined}
    />
  );
}

export default function Home() {
  return (
    <Suspense fallback={<div className="w-full h-screen bg-slate-950" />}>
      <HomeContent />
    </Suspense>
  );
}
