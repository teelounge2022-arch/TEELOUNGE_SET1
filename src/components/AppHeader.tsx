'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const TABS = [
  { href: '/', label: '재고 지도' },
  { href: '/products', label: '상품 현황' },
] as const;

export default function AppHeader() {
  const pathname = usePathname();

  return (
    <header className="flex h-[52px] flex-none items-center gap-5 border-b border-[#dbe0dd] bg-white px-4 text-[#1b2120] dark:border-[#2f3734] dark:bg-[#1c2220] dark:text-[#e7ece9]">
      <div className="flex items-baseline gap-1.5 whitespace-nowrap">
        <b className="text-[15px] font-bold tracking-wide">TEE LOUNGE</b>
        <span className="text-[13px] font-medium text-[#5d6864] dark:text-[#9aa5a0]">AI 업무실</span>
      </div>
      <nav aria-label="업무실 메뉴" className="flex self-stretch">
        {TABS.map((tab) => {
          const active = tab.href === '/' ? pathname === '/' : pathname.startsWith(tab.href);
          return (
            <Link
              key={tab.href}
              href={tab.href}
              aria-current={active ? 'page' : undefined}
              className={`relative flex items-center px-3 text-sm ${
                active
                  ? 'font-semibold after:absolute after:inset-x-2.5 after:-bottom-px after:h-0.5 after:rounded after:bg-[#d9561f] dark:after:bg-[#f0743a]'
                  : 'font-medium text-[#5d6864] hover:text-[#1b2120] dark:text-[#9aa5a0] dark:hover:text-[#e7ece9]'
              }`}
            >
              {tab.label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}
