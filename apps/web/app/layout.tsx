import type { Metadata } from "next";
import Link from "next/link";
import { Geist } from "next/font/google";
import "./globals.css";

const geist = Geist({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "Novel Forge",
  description: "Story gene analysis and novel writing assistant",
};

const NAV_ITEMS = [
  { href: "/", label: "仪表盘", icon: "📊" },
  { href: "/projects", label: "小说项目", icon: "📖" },
  { href: "/library", label: "资料库", icon: "📚" },
  { href: "/settings", label: "设置", icon: "⚙️" },
];

function Sidebar() {
  return (
    <aside className="w-56 bg-gray-900 text-gray-100 flex flex-col shrink-0">
      <div className="px-4 py-4 border-b border-gray-700">
        <Link href="/" className="text-lg font-bold tracking-wide">
          Novel Forge
        </Link>
      </div>
      <nav className="flex-1 px-2 py-3 space-y-1">
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="flex items-center gap-2 px-3 py-2 rounded-md text-sm hover:bg-gray-800 transition-colors"
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>
      <div className="px-4 py-3 border-t border-gray-700 text-xs text-gray-500">
        v0.1.0
      </div>
    </aside>
  );
}

function TopBar() {
  return (
    <header className="h-12 bg-white border-b flex items-center px-6 shrink-0">
      <span className="text-sm text-gray-500">网文故事基因与长篇创作辅助系统</span>
    </header>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className={`h-full ${geist.variable} antialiased`}>
      <body className="h-full flex bg-gray-50 text-gray-900 font-[family-name:var(--font-sans)]">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <TopBar />
          <main className="flex-1 overflow-auto p-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
