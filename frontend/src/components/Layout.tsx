import { useEffect, useState, type ReactNode } from "react";

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem("fashion-theme") === "dark";
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
    localStorage.setItem("fashion-theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  return (
    <div className="min-h-screen bg-[#fafafa] text-gray-900 transition-colors duration-300 dark:bg-[#0a0a0a] dark:text-gray-100">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-gray-200/80 bg-white/90 backdrop-blur-xl transition-colors dark:border-white/10 dark:bg-[#0a0a0a]/90">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gray-900 text-lg font-bold text-white shadow-sm dark:bg-white dark:text-gray-900">
              F
            </div>

            <div>
              <h1 className="text-lg font-bold tracking-tight text-gray-900 dark:text-white">
                Fashion Search
              </h1>

              <p className="hidden text-xs text-gray-500 dark:text-gray-400 sm:block">
                Intelligent fashion discovery
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden items-center gap-6 text-sm text-gray-500 md:flex">
              <span className="font-medium text-gray-900 dark:text-white">
                Discover
              </span>

              <span className="text-gray-500 dark:text-gray-400">
                How it works
              </span>

              <span className="rounded-full border border-gray-200 bg-gray-50 px-3 py-1.5 text-xs font-medium text-gray-600 dark:border-white/10 dark:bg-white/5 dark:text-gray-300">
                AI Powered
              </span>
            </div>

            {/* Theme Toggle */}
            <button
              type="button"
              onClick={() => setDarkMode((current) => !current)}
              aria-label={
                darkMode ? "Switch to light mode" : "Switch to dark mode"
              }
              className="flex h-10 w-10 items-center justify-center rounded-xl border border-gray-200 bg-white text-gray-600 shadow-sm transition hover:bg-gray-50 hover:text-gray-900 dark:border-white/10 dark:bg-white/5 dark:text-gray-300 dark:hover:bg-white/10 dark:hover:text-white"
            >
              {darkMode ? (
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="4" />
                  <path d="M12 2v2" />
                  <path d="M12 20v2" />
                  <path d="m4.93 4.93 1.41 1.41" />
                  <path d="m17.66 17.66 1.41 1.41" />
                  <path d="M2 12h2" />
                  <path d="M20 12h2" />
                  <path d="m6.34 17.66-1.41 1.41" />
                  <path d="m19.07 4.93-1.41 1.41" />
                </svg>
              ) : (
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </header>

      <main>{children}</main>

      <footer className="mt-20 border-t border-gray-200 bg-white transition-colors dark:border-white/10 dark:bg-[#0a0a0a]">
        <div className="mx-auto flex max-w-7xl flex-col gap-2 px-6 py-8 text-sm text-gray-500 sm:flex-row sm:items-center sm:justify-between lg:px-8">
          <p>Fashion Search · Semantic discovery powered by AI</p>

          <p>Amazon Fashion catalogue</p>
        </div>
      </footer>
    </div>
  );
}