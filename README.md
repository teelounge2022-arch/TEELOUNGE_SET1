# TEE LOUNGE AI 업무실

사무실 재고 위치와 상품 현황을 한곳에서 보는 사내 업무 화면이에요. Next.js + Supabase 로 만들었어요.

## 화면

| 탭 | 주소 | 내용 |
| --- | --- | --- |
| 재고 지도 (메인) | `/` | 사무실 3D 모형에서 재고를 검색하면 어느 선반 몇 단에 있는지 보여줘요. 재고 추가 · 수정 · 엑셀 붙여넣기 · 내보내기를 할 수 있어요. 키보드 숫자 1~6은 구역 이동, 0은 전체 보기예요. |
| 상품 현황 | `/products` | `sabangnet_products` 테이블의 상품을 격자로 보여줘요. |

## 처음 설정

1. 환경 변수 `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` 를 넣어요.
2. Supabase 대시보드의 SQL Editor 에서 [`supabase/stock_items.sql`](supabase/stock_items.sql) 을 한 번 실행해요. 실행 전에는 재고 지도가 예시 데이터만 보여줘요.

> 지금 설정은 사이트 주소를 아는 사람 누구나 재고를 고칠 수 있어요. 외부에 공개된 주소라면 로그인을 붙이고 SQL 의 정책을 `authenticated` 로 바꾸세요.

## 개발

```bash
npm install
npm run dev
```

[http://localhost:3000](http://localhost:3000) 을 열면 재고 지도가 먼저 보여요.

사무실 배치(선반 위치 · 크기 · 단 수)는 `src/components/stock-map/engine.js` 의 `UNITS` 와 가구 배치 코드에 있어요.
