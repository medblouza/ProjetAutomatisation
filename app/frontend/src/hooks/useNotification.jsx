import React, { createContext, useContext, useState, useCallback } from 'react';
import { X, CheckCircle2, AlertTriangle, AlertCircle, Info } from 'lucide-react';

const NotificationContext = createContext(null);

export const NotificationProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback((message, type = 'info', duration = 4000) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);

    if (duration) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
  }, [removeToast]);

  const getIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0" />;
      case 'info':
      default:
        return <Info className="w-5 h-5 text-blue-500 shrink-0" />;
    }
  };

  const getTypeStyles = (type) => {
    switch (type) {
      case 'success':
        return 'border-emerald-500/20 bg-emerald-50/90 dark:bg-emerald-950/20 text-emerald-900 dark:text-emerald-200';
      case 'error':
        return 'border-rose-500/20 bg-rose-50/90 dark:bg-rose-950/20 text-rose-900 dark:text-rose-200';
      case 'warning':
        return 'border-amber-500/20 bg-amber-50/90 dark:bg-amber-950/20 text-amber-900 dark:text-amber-200';
      case 'info':
      default:
        return 'border-blue-500/20 bg-blue-50/90 dark:bg-blue-950/20 text-blue-900 dark:text-blue-200';
    }
  };

  return (
    <NotificationContext.Provider value={{ addToast, removeToast }}>
      {children}

      {/* Toast rendering portal container */}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-md w-full sm:w-auto">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`flex items-start gap-3 p-4 rounded-xl border glass shadow-lg transition-all duration-300 animate-fade-in ${getTypeStyles(toast.type)}`}
          >
            {getIcon(toast.type)}
            <div className="flex-1 text-sm font-medium pr-2">{toast.message}</div>
            <button
              onClick={() => removeToast(toast.id)}
              className="p-0.5 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 transition-colors shrink-0"
            >
              <X className="w-4 h-4 opacity-60 hover:opacity-100" />
            </button>
          </div>
        ))}
      </div>
    </NotificationContext.Provider>
  );
};

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};
export default useNotification;
