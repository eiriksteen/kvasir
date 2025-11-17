import { useEffect, useState, useMemo } from 'react';
import { UUID } from 'crypto';
import { usePipeline, usePipelines } from '@/hooks/usePipelines';
import { useRuns } from '@/hooks/useRuns';
import { useDatasets } from '@/hooks/useDatasets';
import { useDataSources } from '@/hooks/useDataSources';
import { useModelEntities } from '@/hooks/useModelEntities';
import { useProject } from '@/hooks/useProject';
import { SquarePlay, Info, FileText, ArrowDownRight, Trash2 } from 'lucide-react';
import { Dataset } from '@/types/data-objects';
import { DataSource } from '@/types/data-sources';
import { ModelInstantiated } from '@/types/model';
import { RunInDB } from '@/types/runs';
import { mutate } from 'swr';
import ConfirmationPopup from '@/components/ConfirmationPopup';
import JsonSchemaViewer from '@/components/JsonSchemaViewer';
import { DataSourceMini, DatasetMini, ModelEntityMini } from '@/components/entity-mini';

export type ViewType = 'overview' | 'runs';

interface PipelineInfoTabProps {
  pipelineId: UUID;
  projectId: UUID;
  onClose: () => void;
  onDelete?: () => void;
  initialView?: ViewType;
}

export default function PipelineInfoTab({ 
  pipelineId,
  projectId,
  onClose,
  onDelete,
  initialView
}: PipelineInfoTabProps) {

  const { pipeline } = usePipeline(pipelineId, projectId);
  const { deletePipeline } = usePipelines(projectId);
  const { runs } = useRuns(projectId);
  const { datasets } = useDatasets(projectId);
  const { dataSources } = useDataSources(projectId);
  const { modelsInstantiated } = useModelEntities(projectId);
  const { getEntityGraphNode } = useProject(projectId);
  
  const isInProgress = !pipeline?.implementation;
  const [currentView, setCurrentView] = useState<ViewType>(
    initialView || 'overview'
  );
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Get pipeline graph node for inputs
  const pipelineNode = useMemo(() => {
    return pipeline ? getEntityGraphNode(pipeline.id) : null;
  }, [pipeline, getEntityGraphNode]);

  const handleDelete = async () => {
    try {
      await deletePipeline({ pipelineId });
      onDelete?.();
      onClose();
    } catch (error) {
      console.error('Failed to delete pipeline:', error);
    }
  };

  // Find the run that has this pipeline in its outputs
  const pipelineAgentRun: RunInDB | undefined = useMemo(() => {
    return runs.find(run => {
      const runNode = getEntityGraphNode(run.id);
      return runNode?.toEntities.pipelines.includes(pipelineId);
    });
  }, [runs, pipelineId, getEntityGraphNode]);

  // Update view when initialView changes (e.g., when clicking runs box on already-open tab)
  useEffect(() => {
    if (initialView && !isInProgress) {
      setCurrentView(initialView);
    }
  }, [initialView, isInProgress]);

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


  // Update the info when the pipeline implementation completes
  useEffect(() => {
    if (pipelineAgentRun && pipelineAgentRun.status === 'completed') {
      mutate(["pipelines", projectId]);
    }
  }, [pipelineAgentRun, pipeline, projectId]);

  if (!pipeline) {
    return null;
  }

  return (
    <div className="w-full h-full bg-white overflow-hidden flex flex-col">
      {/* Top Buttons */}
      <div className="flex items-center justify-between px-4 py-4">
        <div className="flex gap-2">
        {!isInProgress && (
          <button
            onClick={() => setCurrentView('overview')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
              currentView === 'overview'
                ? 'bg-[#840B08] text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <Info className="w-4 h-4" />
          </button>
        )}
        <button
          onClick={() => setCurrentView('runs')}
          disabled={isInProgress}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
            currentView === 'runs'
              ? 'bg-[#840B08] text-white'
              : isInProgress
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <SquarePlay className="w-4 h-4" />
        </button>
        </div>
        <button
          onClick={() => setShowDeleteConfirm(true)}
          className="p-2 text-red-800 hover:bg-red-100 rounded-lg transition-colors"
          title="Delete pipeline"
        >
          <Trash2 size={18} />
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 min-h-0 overflow-hidden">

        {currentView === 'runs' && !isInProgress && (
          <div className="h-full overflow-y-auto p-4">
            {!pipeline.runs || pipeline.runs.length === 0 ? (
              <div className="flex items-center justify-center h-full text-center">
                <p className="text-sm text-gray-500">No runs yet</p>
              </div>
            ) : (
              <div className="space-y-2">
                {pipeline.runs.map((run) => (
                  <div key={run.id} className="bg-white border border-gray-200 rounded-lg p-3">
                    <div className="flex justify-between items-start mb-2">
                      <p className="text-sm text-gray-700 font-medium">
                        {run.name || `Run ${run.id.slice(0, 8)}`}
                      </p>
                      <span className={`text-xs font-mono px-2 py-1 rounded ${
                        run.status === 'completed' 
                          ? 'bg-green-100 text-green-800' 
                          : run.status === 'failed' 
                          ? 'bg-red-100 text-red-800' 
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>{run.status}</span>
                    </div>
                    {run.description && (
                      <p className="text-xs text-gray-600 mb-2">{run.description}</p>
                    )}
                    <div className="text-xs text-gray-500">
                      <p>Started: {new Date(run.startTime).toLocaleString()}</p>
                      {run.endTime && (
                        <p>Ended: {new Date(run.endTime).toLocaleString()}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {currentView === 'overview' && !isInProgress && (
          <div className="h-full overflow-y-auto pl-4 pr-4 pb-4 space-y-4">
            {/* Docstring */}
            {pipeline.implementation?.docstring ? (
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
                  {pipeline.implementation.docstring}
                </pre>
              </div>
            ) : (
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <p className="text-sm text-gray-400 italic">No documentation available</p>
              </div>
            )}

            {/* Four Separate Boxes - Perfect 2x2 Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4" style={{gridTemplateRows: 'auto auto'}}>
              {/* Output Variables Schema Box */}
              {pipeline.implementation?.outputVariablesSchema && Object.keys(pipeline.implementation.outputVariablesSchema).length > 0 && (
                <div className="bg-gray-50 rounded-xl p-4 lg:col-span-2 flex flex-col min-h-0">
                  <JsonSchemaViewer
                    schema={pipeline.implementation.outputVariablesSchema}
                    title="Output Variables Schema"
                    icon={FileText}
                    className="flex-1 min-h-0"
                  />
                </div>
              )}

              {/* Input Entities Box */}
              {pipelineNode && (
                <div className="bg-gray-50 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="p-1.5 bg-[#840B08]/20 rounded-lg">
                      <ArrowDownRight size={16} className="text-[#840B08]" />
                    </div>
                    <h4 className="text-sm font-semibold text-gray-900">Input Entities</h4>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {pipelineNode.fromEntities.dataSources.map((dataSourceId) => {
                      const dataSource = dataSources?.find((ds: DataSource) => ds.id === dataSourceId);
                      return (
                        <DataSourceMini
                          key={dataSourceId}
                          name={dataSource?.name || 'Data Source'}
                          size="sm"
                        />
                      );
                    })}
                    {pipelineNode.fromEntities.datasets.map((datasetId) => {
                      const dataset = datasets?.find((ds: Dataset) => ds.id === datasetId);
                      return (
                        <DatasetMini
                          key={datasetId}
                          name={dataset?.name || 'Dataset'}
                          size="sm"
                        />
                      );
                    })}
                    {pipelineNode.fromEntities.modelsInstantiated.map((modelInstantiatedId) => {
                      const modelInstantiated = modelsInstantiated?.find((me: ModelInstantiated) => me.id === modelInstantiatedId);
                      return (
                        <ModelEntityMini
                          key={modelInstantiatedId}
                          name={modelInstantiated?.name || 'Model'}
                          size="sm"
                        />
                      );
                    })}
                    {pipelineNode.fromEntities.dataSources.length === 0 &&
                     pipelineNode.fromEntities.datasets.length === 0 &&
                     pipelineNode.fromEntities.modelsInstantiated.length === 0 && (
                      <p className="text-sm text-gray-400 italic">No input entities</p>
                    )}
                  </div>
                </div>
              )}

            </div>

          </div>
        )}
      </div>
      
      <ConfirmationPopup
        message={`Are you sure you want to delete "${pipeline.name}"? This will permanently delete the pipeline and all its runs. This action cannot be undone.`}
        isOpen={showDeleteConfirm}
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteConfirm(false)}
      />
    </div>
  );
}