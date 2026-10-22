'use client';

import { useEffect, useRef } from 'react';
import { createStockStore } from '@/lib/stockStore';
import './stockmap.css';

// 3D 엔진은 브라우저에서만 불러와요 (three.js 가 서버 렌더링에 들어가지 않게)
export default function StockMap() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cleanup: (() => void) | undefined;
    let cancelled = false;
    Promise.all([import('./engine'), createStockStore()]).then(([{ mountStockMap }, store]) => {
      if (cancelled || !ref.current) return;
      cleanup = mountStockMap(ref.current, store);
    });
    return () => {
      cancelled = true;
      cleanup?.();
    };
  }, []);

  return <div ref={ref} className="stockmap" />;
}
