import React from 'react';
import { Bell } from 'lucide-react';

interface ToastProps {
  message: string | null;
}

export const Toast: React.FC<ToastProps> = ({ message }) => {
  if (!message) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-bounce">
      <div className="glass-panel border-cyan-500/50 bg-slate-900/95 text-cyan-200 px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 border shadow-cyan-500/20 max-w-md">
        <div className="p-2 rounded-lg bg-cyan-500/20 text-cyan-400 shrink-0">
          <Bell className="w-4 h-4 animate-pulse" />
        </div>
        <div className="text-xs font-semibold leading-snug">{message}</div>
      </div>
    </div>
  );
};
