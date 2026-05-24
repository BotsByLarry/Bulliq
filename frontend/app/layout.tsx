import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Bulliq AI Advisory Console",
  description: "Multi-user 10-Layer AI Investment and Day Trading Terminal",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body>
        <div className="flex flex-col min-h-screen">
          {/* Main Top Header */}
          <header className="border-b border-[rgba(255,255,255,0.06)] bg-[rgba(10,14,23,0.7)] backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded bg-gradient-to-tr from-[#00f2fe] to-[#4facfe] flex items-center justify-center font-bold text-slate-950 text-lg">
                B
              </div>
              <span className="font-bold text-lg tracking-wide bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                Bulliq AI Terminal
              </span>
            </div>
            
            <div className="flex items-center gap-6 text-sm text-[var(--text-secondary)]">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[var(--color-bullish)] pulse-active"></span>
                <span className="font-medium text-slate-300">Sandbox Simulated Feed</span>
              </div>
              <div className="h-4 w-[1px] bg-slate-800"></div>
              <span>Multi-User System Active</span>
            </div>
          </header>

          <main className="flex-1 flex flex-col">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
