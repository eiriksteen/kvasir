import { format } from 'date-fns';
import { X } from 'lucide-react';
import { useEffect } from 'react';
import DatasetOverview from './DatasetOverview';
import IntegrationView from './IntegrationView';
import { useTimeSeriesDatasetMetadata } from '@/hooks/useTimeSeriesDataset';

interface IntegrationModalProps {
  datasetId: string;
  onClose: () => void;
  gradientClass: string | undefined;
}

export default function IntegrationModal({ datasetId, onClose, gradientClass }: IntegrationModalProps) {
  const { dataset } = useTimeSeriesDatasetMetadata(datasetId);

  // Prevent body scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  // Handle escape key to close modal
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  if (!dataset) return null;

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
            <h2 className="text-base font-mono text-gray-200">{dataset.name}</h2>
            <div className="flex-1" />
            <div className="text-xs font-mono text-gray-500">
              Updated {format(new Date(dataset.updatedAt), 'MMM d, yyyy')}
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
            {/* Left Panel - Dataset Overview */}
            <div className="w-1/2 flex flex-col min-h-0">
              <div className="flex-1 overflow-y-auto">
                <DatasetOverview dataset={dataset} />
              </div>
            </div>
            
            {/* Right Panel - Integration View */}
            <div className="w-1/2 flex flex-col min-h-0">
              <IntegrationView datasetId={datasetId} />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}


