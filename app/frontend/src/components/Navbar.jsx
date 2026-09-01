import React, { useEffect, useState } from 'react';
import { Menu, Sun, Moon, ArrowUpRight } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export const Navbar = ({ activeTab, setSidebarOpen }) => {
  const { auth } = useAuth();
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || 'light';
  });

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  const getPageTitle = (tab) => {
    switch (tab) {
      case 'dp':
        return '📊 DP Data Explorer';
      case 'dbx':
        return '📦 Dropbox Asset Manager';
      case 'drive':
        return '📁 Client Shared Folder';
      case 'wireframe':
        return '🎨 Wireframe Builder';
      case 'style':
        return '🖌️ Visual Style Extractor';
      case 'sitegen':
        return '🏗️ Automatic Site Generator';
      default:
        return 'Dashboard';
    }
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-border/40 bg-background/80 backdrop-blur-md px-6">
      {/* Mobile Burger & Page Title */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => setSidebarOpen(true)}
          className="flex h-9 w-9 items-center justify-center rounded-xl border border-border bg-card text-muted-foreground hover:text-foreground lg:hidden"
        >
          <Menu className="h-5 w-5" />
        </button>
        <h1 className="text-base font-extrabold text-foreground select-none md:text-lg">
          {getPageTitle(activeTab)}
        </h1>
      </div>

      {/* Utilities */}
      <div className="flex items-center gap-3">
        {/* Connection status tag */}
        <span className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-emerald-500/20 bg-emerald-500/5 text-[11px] font-bold text-emerald-600 dark:text-emerald-400 select-none">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          API Connected
        </span>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="flex h-9 w-9 items-center justify-center rounded-xl border border-border bg-card text-muted-foreground hover:text-foreground transition-all duration-200"
          title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        >
          {theme === 'dark' ? <Sun className="h-4.5 w-4.5" /> : <Moon className="h-4.5 w-4.5" />}
        </button>
      </div>
    </header>
  );
};

export default Navbar;
