'use client';

import { useEffect } from 'react';
import { X } from 'lucide-react';


interface AddAnalysisProps {
  onClose: () => void;
  projectId: string;
}

export default function AddAnalysis({ onClose, projectId }: AddAnalysisProps) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);


  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl h-[80vh] bg-white border border-gray-300 rounded-lg shadow-2xl overflow-hidden">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 z-50 p-1 rounded-full text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
          title="Close (Esc)"
        >
          <X size={20} />
        </button>

        <div className="flex flex-col h-full">
          <div className="p-4">
            <h3 className="text-xs font-mono uppercase tracking-wider text-gray-600">Add Analysis</h3>
          </div>

        </div>
      </div>
    </div>
  );
} 