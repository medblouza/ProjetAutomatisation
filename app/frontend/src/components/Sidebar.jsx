import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { 
  BarChart3, 
  Box, 
  FolderSymlink, 
  Palette, 
  Brush, 
  Activity,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Menu,
  Sparkles,
  Link2,
  FileText
} from 'lucide-react';
import Badge from './ui/Badge';

export const Sidebar = ({ activeTab, setActiveTab, sidebarOpen, setSidebarOpen }) => {
  const { auth, logout, dbxAccessToken, cleanedData } = useAuth();

  const navigationItems = [
    { id: 'dp', label: 'DP Explorer', icon: BarChart3 },
    { id: 'dbx', label: 'Dropbox', icon: Box, badge: dbxAccessToken ? 'Connected' : null, badgeVariant: 'success' },
    { id: 'drive', label: 'Dossier partagé', icon: FolderSymlink },
    { id: 'wireframe', label: 'Wireframe', icon: Palette, badge: cleanedData ? 'Ready' : null, badgeVariant: 'primary' },
    { id: 'style', label: 'Style Extractor', icon: Brush },
    { id: 'sitegen', label: 'Site Generator', icon: Activity },
    { id: 'cdc', label: 'CDC / JSON', icon: FileText },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden transition-opacity"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar Panel */}
      <aside 
        className={`fixed top-0 bottom-0 left-0 z-45 flex flex-col border-r border-border/80 bg-card/95 backdrop-blur-md transition-all duration-300 ${
          sidebarOpen ? 'w-64 translate-x-0' : 'w-20 -translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Header Branding */}
        <div className="flex h-16 items-center justify-between px-6 border-b border-border/40">
          <div className="flex items-center gap-2.5 font-bold text-foreground">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-md shadow-primary/20 shrink-0">
              <Sparkles className="h-5 w-5" />
            </div>
            {sidebarOpen && (
              <span className="text-base font-extrabold tracking-tight bg-gradient-to-r from-primary to-indigo-500 bg-clip-text text-transparent">
                DP Explorer
              </span>
            )}
          </div>
          
          <button 
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="hidden lg:flex h-7 w-7 items-center justify-center rounded-lg border border-border bg-card text-muted-foreground hover:text-foreground hover:bg-secondary/80 shrink-0"
          >
            {sidebarOpen ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 space-y-1.5 px-4 py-6 overflow-y-auto">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id);
                  // Close on mobile
                  if (window.innerWidth < 1024) {
                    setSidebarOpen(false);
                  }
                }}
                className={`w-full flex items-center gap-3 rounded-xl px-4 py-3.5 text-sm font-semibold transition-all duration-200 select-none group relative ${
                  isActive 
                    ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/10' 
                    : 'text-muted-foreground hover:text-foreground hover:bg-secondary/60'
                }`}
              >
                <Icon className={`h-5 w-5 shrink-0 ${isActive ? 'text-current' : 'text-muted-foreground group-hover:text-foreground'}`} />
                {sidebarOpen && (
                  <span className="flex-1 text-left truncate">{item.label}</span>
                )}
                {sidebarOpen && item.badge && (
                  <Badge variant={item.badgeVariant} className="ml-auto text-[10px] px-2 py-0.5 font-bold shrink-0">
                    {item.badge}
                  </Badge>
                )}
                
                {/* Tooltip when collapsed */}
                {!sidebarOpen && (
                  <div className="absolute left-full ml-4 hidden group-hover:block z-50 bg-popover text-popover-foreground border border-border shadow-xl px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap">
                    {item.label}
                    {item.badge && ` (${item.badge})`}
                  </div>
                )}
              </button>
            );
          })}
        </nav>

        {/* User Footer Profile */}
        <div className="p-4 border-t border-border/40 bg-muted/10 rounded-b-2xl">
          <div className={`flex items-center gap-3 ${sidebarOpen ? 'justify-between' : 'justify-center'}`}>
            {sidebarOpen && (
              <div className="min-w-0">
                <p className="text-sm font-bold text-foreground truncate select-none">
                  {auth?.username || 'Guest'}
                </p>
                <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-extrabold select-none">
                  Sage Account
                </span>
              </div>
            )}
            
            <button
              onClick={logout}
              title="Deconnexion"
              className="flex h-9 w-9 items-center justify-center rounded-xl border border-border bg-card text-muted-foreground hover:text-rose-500 hover:border-rose-500/20 hover:bg-rose-50 dark:hover:bg-rose-950/20 transition-all shrink-0"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
