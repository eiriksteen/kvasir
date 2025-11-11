'use client';

import { useState, useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import { useAnalyses } from '@/hooks/useAnalysis';
import { AnalysisCreate } from '@/types/analysis';
import { UUID } from 'crypto';

interface AddAnalysisProps {
  onClose: () => void;
  projectId: UUID;
}

export default function AddAnalysis({ projectId, onClose }: AddAnalysisProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const { createAnalysis } = useAnalyses(projectId);
  const backdropRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (backdropRef.current && event.target === backdropRef.current) {
        onClose();
      }
    };

    const backdrop = backdropRef.current;
    if (backdrop) {
      backdrop.addEventListener('click', handleClickOutside);
      return () => backdrop.removeEventListener('click', handleClickOutside);
    }
  }, [onClose]);

  const handleSubmit = async () => {
    const analysisCreate: AnalysisCreate = {
      name,
      description: description || null
    };
    await createAnalysis(analysisCreate);
    setName('');
    setDescription('');
    onClose();
  };

  return (
    <div ref={backdropRef} className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl h-[80vh] bg-white border border-gray-300 rounded-lg shadow-2xl overflow-hidden">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 z-50 p-1 rounded-full text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
          title="Close (Esc)"
        >
          <X size={20} />
        </button>

        <div className="flex flex-col h-full p-4">
          <h3 className="text-xs font-mono uppercase tracking-wider text-gray-600 mb-6">Add Analysis</h3>
          
          {/* Analysis Name */}
          <div className="mb-4">
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
              Analysis Name
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full p-2 bg-white border border-gray-300 rounded text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-[#0E4F70] focus:border-[#0E4F70] transition-all duration-200"
              placeholder="Enter analysis name..."
            />
          </div>

          {/* Analysis Description */}
          <div className="mb-4">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full h-full p-2 bg-white border border-gray-300 rounded text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-[#0E4F70] focus:border-[#0E4F70] transition-all duration-200 resize-none text-sm"
              placeholder="Describe what you want to analyze..."
            />
          </div>

          {/* Submit Button */}
          <div className="mt-auto border-gray-300">
            <button
              onClick={handleSubmit}
              disabled={!name.trim()}
              className="w-full h-10 flex items-center justify-center gap-2 px-4 bg-[#0E4F70] hover:bg-[#0E4F70]/80 disabled:bg-gray-300 disabled:text-gray-500 text-white font-medium rounded-lg transition-all duration-200 disabled:cursor-not-allowed"
            >
              Create Analysis
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}