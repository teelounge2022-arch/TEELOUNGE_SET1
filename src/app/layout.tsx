import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans_KR } from "next/font/google";
import AppHeader from "@/components/AppHeader";
import "./globals.css";

const plexKr = IBM_Plex_Sans_KR({
  variable: "--font-plex-kr",
  weight: ["400", "500", "600", "700"],
  preload: false,
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  weight: ["500", "600"],
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "TEE LOUNGE AI 업무실",
  description: "재고 지도와 상품 현황을 한곳에서 보는 TEE LOUNGE 업무 화면",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="ko"
      className={`${plexKr.variable} ${plexMono.variable} h-full antialiased`}
    >
      <body className="h-full flex flex-col">
        <AppHeader />
        <div className="flex min-h-0 flex-1 flex-col overflow-auto">{children}</div>
      </body>
    </html>
  );
}
