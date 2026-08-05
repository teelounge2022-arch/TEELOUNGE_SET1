'use client';

import { useState } from 'react';
import { supabase } from '@/lib/supabase';
import { Loader2 } from 'lucide-react';

export default function ProductGrid({ initialProducts, initialCount }: { initialProducts: any[], initialCount: number }) {
  const [products, setProducts] = useState(initialProducts);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(initialProducts.length < initialCount);
  const PAGE_SIZE = 100; // Load 100 items at a time for high density

  const loadMore = async () => {
    if (loading || !hasMore) return;
    setLoading(true);
    
    const from = page * PAGE_SIZE;
    const to = from + PAGE_SIZE - 1;
    
    const { data, error } = await supabase
      .from('sabangnet_products')
      .select('*')
      .order('id', { ascending: true })
      .range(from, to);

    if (error) {
      console.error(error);
      setLoading(false);
      return;
    }

    if (data && data.length > 0) {
      setProducts(prev => [...prev, ...data]);
      setPage(p => p + 1);
      if (data.length < PAGE_SIZE) {
        setHasMore(false);
      }
    } else {
      setHasMore(false);
    }
    setLoading(false);
  };

  return (
    <div className="w-full max-w-[1920px] mx-auto p-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-900">전체 상품 현황</h1>
        <div className="text-sm text-slate-500 font-medium">총 {initialCount.toLocaleString()}개 상품</div>
      </div>
      
      {/* High Density Grid: 2 cols on mobile, 4 on tablet, 6 on small desktop, 8 on wide, 10 on ultrawide */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 2xl:grid-cols-10 gap-3">
        {products.map((product) => (
          <div key={product.id} className="group flex flex-col bg-white border border-slate-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow duration-200">
            {/* Image Container (1:1 Aspect Ratio) */}
            <div className="relative w-full pt-[100%] bg-slate-100 overflow-hidden">
              {product.main_image ? (
                <img 
                  src={product.main_image} 
                  alt={product.product_name || '상품 이미지'} 
                  className="absolute top-0 left-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  loading="lazy"
                />
              ) : (
                <div className="absolute top-0 left-0 w-full h-full flex items-center justify-center text-slate-400 text-xs">No Image</div>
              )}
            </div>
            
            {/* Content Area */}
            <div className="p-3 flex flex-col flex-grow justify-between gap-2">
              <div>
                <div className="text-[10px] font-semibold text-slate-500 mb-1 line-clamp-1">
                  {product.brand || '브랜드 없음'}
                </div>
                <h3 className="text-xs font-medium text-slate-900 line-clamp-2 leading-snug" title={product.product_name}>
                  {product.product_name || '상품명 없음'}
                </h3>
              </div>
              
              <div className="flex flex-col mt-1">
                {product.tag_price && product.tag_price !== product.sale_price && (
                  <span className="text-[10px] text-slate-400 line-through">
                    {product.tag_price.includes(',') ? product.tag_price : Number(product.tag_price).toLocaleString()}원
                  </span>
                )}
                <span className="text-sm font-bold text-slate-900">
                  {product.sale_price?.includes(',') ? product.sale_price : Number(product.sale_price || 0).toLocaleString()}원
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {hasMore && (
        <div className="mt-10 flex justify-center pb-10">
          <button 
            onClick={loadMore} 
            disabled={loading}
            className="flex items-center gap-2 px-8 py-3 bg-slate-900 text-white text-sm font-medium rounded-full hover:bg-slate-800 transition-colors disabled:opacity-50"
          >
            {loading && <Loader2 className="w-4 h-4 animate-spin" />}
            {loading ? '불러오는 중...' : '상품 더 보기'}
          </button>
        </div>
      )}
    </div>
  );
}
