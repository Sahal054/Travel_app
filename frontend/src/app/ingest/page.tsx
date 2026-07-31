'use client';

import dynamic from 'next/dynamic';

const IngestMapCanvas = dynamic(() => import('@/components/IngestMapCanvas'), {
  ssr: false,
  loading: () => <div className="w-full h-screen bg-slate-950" />,
});

export default function IngestPage() {
  return <IngestMapCanvas />;
}
