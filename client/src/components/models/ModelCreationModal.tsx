import { format } from 'date-fns';
import { X, Loader2 } from 'lucide-react';
import { useEffect } from 'react';
import ModelIntegrationChat from './ModelIntegrationChat';
import { Run } from '@/types/runs';

interface ModelCreationModalProps {
  job: Run;
  onClose: () => void;
  gradientClass: string | undefined;
}

export default function ModelCreationModal({ job, onClose, gradientClass }: ModelCreationModalProps) {

  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  return (
    <>
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
        onClick={onClose}
      />
      
      <div className="fixed inset-4 z-50 flex items-center justify-center">
        <div className="relative bg-[#050a14] rounded-xl p-6 border-2 border-[#101827] w-full max-w-7xl h-full max-h-[90vh] flex flex-col overflow-hidden shadow-2xl">
          {gradientClass && (
            <div className={`absolute inset-0 bg-gradient-to-br ${gradientClass} opacity-5 rounded-xl pointer-events-none`} />
          )}
          
          <div className="relative flex items-center gap-2 mb-4">
            <h2 className="text-base font-mono text-gray-200">{job.jobName || 'Model Being Created'}</h2>
            <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
            <div className="flex-1" />
            <div className="text-xs font-mono text-gray-500">
              Started {format(new Date(job.startedAt), 'MMM d, yyyy')}
            </div>
            <button
              onClick={onClose}
              className="text-zinc-400 hover:text-zinc-300 transition-colors ml-2"
              title="Close visualization"
            >
              <X size={20} />
            </button>
          </div>
          
          {/* Main Content - Side by Side Layout */}
          <div className="relative flex-1 min-h-0 flex gap-6">
            {/* Left Panel - Model Overview Placeholder */}
            <div className="w-1/2 flex flex-col min-h-0">
              <div className="flex-1 overflow-y-auto flex items-center justify-center">
                <div className="text-center">
                  <p className="text-sm text-zinc-500">
                    The model is being created. A model overview will show up here once it&apos;s ready.
                  </p>
                </div>
              </div>
            </div>
            
            {/* Right Panel - Integration Chat */}
            <div className="w-1/2 flex flex-col min-h-0">
              <ModelIntegrationChat job={job} />
            </div>
          </div>
        </div>
      </div>
    </>
  );
} 