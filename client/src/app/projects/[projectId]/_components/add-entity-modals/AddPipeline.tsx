'use client';

import { useEffect } from 'react';
import { X } from 'lucide-react';


interface AddPipelineProps {
  onClose: () => void;
  projectId: string;
}

export default function AddPipeline({ onClose, projectId }: AddPipelineProps) {

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
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl h-[80vh] bg-gray-950 border border-[#101827] rounded-lg shadow-2xl overflow-hidden">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 z-50 p-1 rounded-full text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
          title="Close (Esc)"
        >
          <X size={20} />
        </button>

        <div className="flex flex-col h-full">
          <div className="p-4">
            <h3 className="text-xs font-mono uppercase tracking-wider text-gray-400">Add Pipeline</h3>
          </div>

        </div>
      </div>
    </div>
  );
} 