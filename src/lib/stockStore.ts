// 재고 지도용 Supabase 저장소. 테이블은 supabase/stock_items.sql 로 만들어요.

export type StockRow = {
  id: string;
  name: string;
  color: string;
  size: string;
  qty: number;
  unit: string;
  level: number;
  note: string;
  updatedAt: number;
};

type StockBody = Partial<Omit<StockRow, 'id'>>;
export type StockErrorCode = 'missing_table' | 'forbidden' | 'unavailable';

export type StockStore = {
  canWrite: boolean;
  subscribe(onRows: (rows: StockRow[]) => void, onError: (code: StockErrorCode) => void): () => void;
  add(body: StockBody): Promise<void>;
  update(id: string, body: StockBody): Promise<void>;
  remove(id: string): Promise<void>;
};

const TABLE = 'stock_items';
const FIELDS = ['name', 'color', 'size', 'qty', 'unit', 'level', 'note'] as const;

type DbRow = Record<string, unknown>;
type DbError = { code?: string; message?: string };

function toDb(body: StockBody): DbRow {
  const row: DbRow = {};
  for (const key of FIELDS) if (body[key] !== undefined) row[key] = body[key];
  row.updated_at = new Date(body.updatedAt ?? Date.now()).toISOString();
  return row;
}

function fromDb(row: DbRow): StockRow {
  return {
    id: String(row.id),
    name: String(row.name ?? ''),
    color: String(row.color ?? ''),
    size: String(row.size ?? ''),
    qty: Number(row.qty ?? 0),
    unit: String(row.unit ?? ''),
    level: Number(row.level ?? 1),
    note: String(row.note ?? ''),
    updatedAt: row.updated_at ? Date.parse(String(row.updated_at)) : 0,
  };
}

function codeOf(error: DbError): StockErrorCode {
  const msg = error.message ?? '';
  if (error.code === 'PGRST205' || error.code === '42P01' || /could not find the table|does not exist/i.test(msg)) return 'missing_table';
  if (error.code === '42501' || /row-level security|permission denied/i.test(msg)) return 'forbidden';
  return 'unavailable';
}

/** Supabase 환경 변수가 없으면 null 을 돌려줘요. 그때 지도는 예시 데이터만 보여줘요. */
export async function createStockStore(): Promise<StockStore | null> {
  if (!process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) return null;
  const { supabase } = await import('@/lib/supabase');
  let reload = () => {};

  const run = async (op: PromiseLike<{ error: DbError | null }>) => {
    const { error } = await op;
    if (error) throw { code: codeOf(error), message: error.message };
    reload();
  };

  return {
    canWrite: true,
    subscribe(onRows, onError) {
      let stopped = false;
      let timer: ReturnType<typeof setTimeout> | undefined;
      const load = async () => {
        const { data, error } = await supabase.from(TABLE).select('*').order('unit').limit(5000);
        if (stopped) return;
        if (error) onError(codeOf(error));
        else onRows((data ?? []).map(fromDb));
      };
      reload = () => { clearTimeout(timer); timer = setTimeout(load, 150); };
      load();
      // 다른 사람이 고친 내용은 Realtime 으로 바로, 혹시 꺼져 있어도 30초마다 다시 읽어요
      const channel = supabase
        .channel('stock_items_changes')
        .on('postgres_changes', { event: '*', schema: 'public', table: TABLE }, reload)
        .subscribe();
      const poll = setInterval(load, 30_000);
      return () => {
        stopped = true;
        clearTimeout(timer);
        clearInterval(poll);
        supabase.removeChannel(channel);
      };
    },
    add: (body) => run(supabase.from(TABLE).insert(toDb(body))),
    update: (id, body) => run(supabase.from(TABLE).update(toDb(body)).eq('id', id)),
    remove: (id) => run(supabase.from(TABLE).delete().eq('id', id)),
  };
}
