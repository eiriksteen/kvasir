import { X, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useDataSource } from "@/hooks/useDataSources";
import { UUID } from 'crypto';
import JsonViewer from '@/components/JsonViewer';
import ConfirmationPopup from '@/components/ConfirmationPopup';
import { useOntology } from '@/hooks/useOntology';

interface FileInfoTabProps {
  dataSourceId: UUID;
  projectId: UUID;
  onClose: () => void;
  onDelete?: () => void;
  asModal?: boolean;
}

export default function FileInfoTab({ 
  dataSourceId, 
  projectId,
  onClose,
  onDelete,
  asModal = false
}: FileInfoTabProps) {
  
  const { dataSource } = useDataSource(dataSourceId);
  const { deleteDataSource } = useOntology(projectId);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleDelete = async () => {
    try {
      await deleteDataSource({ dataSourceId });
      onDelete?.();
      onClose();
    } catch (error) {
      console.error('Failed to delete data source:', error);
    }
  };

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
        e.preventDefault();
        e.stopPropagation();
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape, { capture: true });
    return () => document.removeEventListener('keydown', handleEscape, { capture: true });
  }, [onClose]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!dataSource) {
    return null;
  }

  // Check if we have type-specific fields (e.g., tabular file data)
  const typeFields = dataSource.typeFields;

  // Merge general info, typeFields, and additionalVariables into a single object for JSON display
  // Keep general info on top
  const mergedData: Record<string, unknown> = {
    name: dataSource.name,
    type: dataSource.type,
    createdAt: formatDate(dataSource.createdAt),
    ...(typeFields || {}),
    ...(dataSource.additionalVariables || {}),
  };

  const content = (
    <div className="h-full p-4 flex flex-col gap-4">
      <div className="bg-gray-50 rounded-xl p-4 flex-1 min-h-0 flex flex-col relative">
        <div className="absolute top-4 right-4 flex items-center gap-2 z-10">
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="p-2 text-red-800 hover:bg-red-100 rounded-lg transition-colors"
            title="Delete data source"
          >
            <Trash2 size={18} />
          </button>
        </div>
        <JsonViewer 
          data={mergedData} 
          className="flex-1 min-h-0"
        />
      </div>
    </div>
  );

  if (asModal) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
        <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden m-4" onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center justify-end p-4 border-b border-gray-200">
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X size={20} className="text-gray-500" />
            </button>
          </div>
          <div className="overflow-y-auto max-h-[calc(90vh-80px)]">
            {content}
          </div>
        </div>
        <ConfirmationPopup
          message={`Are you sure you want to delete "${dataSource.name}"? This will permanently delete the data source. This action cannot be undone.`}
          isOpen={showDeleteConfirm}
          onConfirm={handleDelete}
          onCancel={() => setShowDeleteConfirm(false)}
        />
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-white overflow-hidden">
      <div className="bg-white h-full px-0 pb-2 relative">
        <div className="flex flex-col h-full">
          <div className="flex-1 min-h-0">
            {content}
          </div>
        </div>
      </div>
      
      <ConfirmationPopup
        message={`Are you sure you want to delete "${dataSource.name}"? This will permanently delete the data source. This action cannot be undone.`}
        isOpen={showDeleteConfirm}
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteConfirm(false)}
      />
    </div>
  );
}