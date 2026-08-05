import { supabase } from '@/lib/supabase';
import ProductGrid from '@/components/ProductGrid';

export const revalidate = 60; // Revalidate every minute

export default async function Home() {
  // Fetch initial total count
  const { count, error: countError } = await supabase
    .from('sabangnet_products')
    .select('*', { count: 'exact', head: true });

  if (countError) {
    console.error("Error fetching count:", countError);
  }

  // Fetch initial 100 products
  const { data: initialProducts, error } = await supabase
    .from('sabangnet_products')
    .select('*')
    .order('id', { ascending: true })
    .limit(100);

  if (error) {
    console.error("Error fetching products:", error);
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 text-red-500">
        데이터를 불러오는데 실패했습니다. 데이터베이스 연결을 확인해주세요.
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50 pt-8">
      <ProductGrid 
        initialProducts={initialProducts || []} 
        initialCount={count || 0} 
      />
    </main>
  );
}
