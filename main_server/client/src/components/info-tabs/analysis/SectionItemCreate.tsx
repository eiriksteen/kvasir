import React, { useRef, useEffect, useState } from 'react';
import { useAnalysisObject } from '@/hooks/useAnalysis';
import { useError } from '@/components/ErrorProvider';
import { Loader2, Plus, X } from 'lucide-react';
import { UUID } from 'crypto';

interface SectionItemCreateProps {
  parentId: UUID | null;
  projectId: UUID;
  analysisObjectId: UUID;
  onCancel: () => void;
}

const SectionItemCreate: React.FC<SectionItemCreateProps> = ({ 
  parentId, 
  projectId, 
  analysisObjectId, 
  onCancel 
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  
  const { createSection } = useAnalysisObject(projectId, analysisObjectId);
  const { showError } = useError();

  useEffect(() => {
    if (inputRef.current) inputRef.current.focus();
  }, []);

  const handleSubmit = async () => {
    if (name.trim() && !isCreating) {
      setIsCreating(true);
      try {
        await createSection({
          sectionName: name.trim(),
          sectionDescription: description.trim() || null,
          parentSectionId: parentId,
        });
        setName('');
        setDescription('');
        onCancel();
      } catch (error) {
        console.error('Error creating section:', error);
        showError(error instanceof Error ? error.message : 'An unknown error occurred');
      } finally {
        setIsCreating(false);
      }
    }
  };

  const isCompact = parentId === null;

  return (
    <div className={`w-full ${isCompact ? 'flex items-center gap-1 my-1' : 'my-3'}`}>
      {isCompact ? (
        <>
          <input
            ref={inputRef}
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="Section name..."
            className="flex-1 px-2 py-1 mr-2 text-xs rounded border border-gray-300 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#0E4F70]"
            onKeyDown={e => {
              if (e.key === 'Enter') handleSubmit();
              if (e.key === 'Escape') onCancel();
            }}
            disabled={isCreating}
          />
          <button
            onClick={handleSubmit}
            disabled={isCreating || !name.trim()}
            className="p-1 text-gray-600 hover:text-gray-900 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isCreating ? <Loader2 size={12} className="animate-spin" /> : <Plus size={12} />}
          </button>
          <button
            onClick={onCancel}
            disabled={isCreating}
            className="p-1 text-gray-600 hover:text-gray-900 transition-colors disabled:cursor-not-allowed"
          >
            <X size={12} /> 
          </button>
        </>
      ) : (
        <div className="space-y-2">
          <div className="flex items-center gap-1">
            <input
              ref={inputRef}
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Section name..."
              className="flex-1 px-3 py-2 mr-3 text-sm rounded border border-gray-300 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#0E4F70]"
              onKeyDown={e => {
                if (e.key === 'Enter') handleSubmit();
                if (e.key === 'Escape') onCancel();
              }}
              disabled={isCreating}
            />
            <button
              onClick={handleSubmit}
              disabled={isCreating || !name.trim()}
              className="p-1 text-gray-600 hover:text-gray-900 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isCreating ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
            </button>
            <button
              onClick={onCancel}
              disabled={isCreating}
              className="p-1 text-gray-600 hover:text-gray-900 transition-colors disabled:cursor-not-allowed"
            >
              <X size={16} /> 
            </button>
          </div>
          <textarea
            value={description}
            onChange={e => setDescription(e.target.value)}
            placeholder="Section description (optional)..."
            className="w-full px-3 py-2 text-sm rounded border border-gray-300 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-[#0E4F70] resize-none"
            rows={3}
            onKeyDown={e => {
              if (e.key === 'Escape') onCancel();
            }}
            disabled={isCreating}
          />
        </div>
      )}
    </div>
  );
};

export default SectionItemCreate; 