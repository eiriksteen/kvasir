import { useEffect, useState, useMemo } from 'react';
import { UUID } from 'crypto';
import { usePipeline, usePipelines } from '@/hooks/usePipelines';
import { useRuns } from '@/hooks/useRuns';
import { useDatasets } from '@/hooks/useDatasets';
import { useDataSources } from '@/hooks/useDataSources';
import { useModelEntities } from '@/hooks/useModelEntities';
import { useAnalyses } from '@/hooks/useAnalysis';
import { SquarePlay, FileCode, Database, Folder, Brain, BarChart3, Info, FileText, ArrowDownRight, ArrowUpRight, Trash2 } from 'lucide-react';
import CodeStream from '@/components/code/CodeStream';
import { Dataset } from '@/types/data-objects';
import { DataSource } from '@/types/data-sources';
import { ModelEntity } from '@/types/model';
import { AnalysisSmall } from '@/types/analysis';
import { Run } from '@/types/runs';
import { mutate } from 'swr';
import ConfirmationPopup from '@/components/ConfirmationPopup';
import JsonSchemaViewer from '@/components/JsonSchemaViewer';

interface PipelineInfoTabProps {
  pipelineId: UUID;
  projectId: UUID;
  onClose: () => void;
  onDelete?: () => void;
}   

type ViewType = 'overview' | 'code' | 'runs';

export default function PipelineInfoTab({ 
  pipelineId,
  projectId,
  onClose,
  onDelete
}: PipelineInfoTabProps) {

  const { pipeline } = usePipeline(pipelineId, projectId);
  const { deletePipeline } = usePipelines(projectId);
  const { runs } = useRuns();
  const { datasets } = useDatasets(projectId);
  const { dataSources } = useDataSources(projectId);
  const { modelEntities } = useModelEntities(projectId);
  const { analysisObjects } = useAnalyses(projectId);
  
  const isInProgress = !pipeline?.implementation;
  const [currentView, setCurrentView] = useState<ViewType>(isInProgress ? 'code' : 'overview');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

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
  const pipelineAgentRun: Run | undefined = useMemo(() => {
    return runs.find(run => 
      run.outputs?.pipelineIds?.includes(pipelineId)
    );
  }, [runs, pipelineId]);

  // When implementation status changes, update the view
  useEffect(() => {
    if (isInProgress && currentView === 'overview') {
      setCurrentView('code');
    }
  }, [isInProgress, currentView]);

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
          onClick={() => setCurrentView('code')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
            currentView === 'code'
              ? 'bg-[#840B08] text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <FileCode className="w-4 h-4" />
          <span className="text-sm font-medium">Code</span>
        </button>
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
          <span className="text-sm font-medium">Runs</span>
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
        {currentView === 'code' && (
          <div className="h-full">
            {!pipeline.implementation ? (
              (pipelineAgentRun ? (
                <CodeStream runId={pipelineAgentRun.id} />
              ) : (
                <div className="flex items-center justify-center h-full text-center">
                  <p className="text-sm text-gray-500">No active run for this pipeline</p>
                </div>
              ))
            ) : (
              <div className="flex items-center justify-center h-full">
                {/* Note: implementationScriptPath is now a string path, not a UUID. Code view not available. */}
                <p className="text-sm text-gray-500">Code view not available - implementation uses script path instead of script ID</p>
              </div>
            )}
          </div>
        )}

        {currentView === 'runs' && !isInProgress && (
          <div className="h-full overflow-y-auto p-4">
            {!pipeline.implementation?.runs || pipeline.implementation.runs.length === 0 ? (
              <div className="flex items-center justify-center h-full text-center">
                <p className="text-sm text-gray-500">No runs yet</p>
              </div>
            ) : (
              <div className="space-y-2">
                {pipeline.implementation.runs.map((run) => (
                  <div key={run.id} className="bg-white border border-gray-200 rounded-lg p-3">
                    <p className="text-sm text-gray-700 mb-2 font-medium">Run {run.id.slice(0, 8)}</p>
                    <p className="text-xs text-gray-600">
                      Status: <span className={`font-mono px-2 py-1 rounded ${
                        run.status === 'completed' 
                          ? 'bg-green-100 text-green-800' 
                          : run.status === 'failed' 
                          ? 'bg-red-100 text-red-800' 
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>{run.status}</span>
                    </p>
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

              {/* Input Entities Box - Bottom Left */}
              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="p-1.5 bg-[#840B08]/20 rounded-lg">
                    <ArrowDownRight size={16} className="text-[#840B08]" />
                  </div>
                  <h4 className="text-sm font-semibold text-gray-900">Input Entities</h4>
                </div>
                <div className="flex flex-wrap gap-1">
                  {pipeline.inputs.dataSourceIds.map((dataSourceId) => (
                    <div
                      key={dataSourceId}
                      className="px-1.5 py-0.5 text-xs rounded-full flex items-center gap-1 bg-gray-200 text-gray-600"
                    >
                      <Database size={10} />
                      {dataSources?.find((ds: DataSource) => ds.id === dataSourceId)?.name || 'Data Source'}
                    </div>
                  ))}
                  {pipeline.inputs.datasetIds.map((datasetId) => (
                    <div
                      key={datasetId}
                      className="px-1.5 py-0.5 text-xs rounded-full flex items-center gap-1 bg-[#0E4F70]/20 text-[#0E4F70]"
                    >
                      <Folder size={10} />
                      {datasets?.find((ds: Dataset) => ds.id === datasetId)?.name || 'Dataset'}
                    </div>
                  ))}
                  {pipeline.inputs.modelEntityIds.map((modelEntityId) => (
                    <div
                      key={modelEntityId}
                      className="px-1.5 py-0.5 text-xs rounded-full flex items-center gap-1 bg-[#491A32]/20 text-[#491A32]"
                    >
                      <Brain size={10} />
                      {modelEntities?.find((me: ModelEntity) => me.id === modelEntityId)?.name || 'Model'}
                    </div>
                  ))}
                  {pipeline.inputs.analysisIds.map((analysisId) => (
                    <div
                      key={analysisId}
                      className="px-1.5 py-0.5 text-xs rounded-full flex items-center gap-1 bg-[#004806]/20 text-[#004806]"
                    >
                      <BarChart3 size={10} />
                      {analysisObjects?.find((a: AnalysisSmall) => a.id === analysisId)?.name || 'Analysis'}
                    </div>
                  ))}
                  {pipeline.inputs.dataSourceIds.length === 0 &&
                   pipeline.inputs.datasetIds.length === 0 &&
                   pipeline.inputs.modelEntityIds.length === 0 &&
                   pipeline.inputs.analysisIds.length === 0 && (
                    <p className="text-sm text-gray-400 italic">No input entities</p>
                  )}
                </div>
              </div>

              {/* Output Entities Box - Bottom Right */}
              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="p-1.5 bg-[#840B08]/20 rounded-lg">
                    <ArrowUpRight size={16} className="text-[#840B08]" />
                  </div>
                  <h4 className="text-sm font-semibold text-gray-900">Output Entities</h4>
                </div>
                <div className="flex flex-wrap gap-1">
                  {pipeline.outputs.datasetIds.map((datasetId) => (
                    <div
                      key={datasetId}
                      className="px-1.5 py-0.5 text-xs rounded-full flex items-center gap-1 bg-[#0E4F70]/20 text-[#0E4F70]"
                    >
                      <Folder size={10} />
                      {datasets?.find((ds: Dataset) => ds.id === datasetId)?.name || 'Dataset'}
                    </div>
                  ))}
                  {pipeline.outputs.modelEntityIds.map((modelEntityId) => (
                    <div
                      key={modelEntityId}
                      className="px-1.5 py-0.5 text-xs rounded-full flex items-center gap-1 bg-[#491A32]/20 text-[#491A32]"
                    >
                      <Brain size={10} />
                      {modelEntities?.find((me: ModelEntity) => me.id === modelEntityId)?.name || 'Model'}
                    </div>
                  ))}
                  {pipeline.outputs.datasetIds.length === 0 &&
                   pipeline.outputs.modelEntityIds.length === 0 && (
                    <p className="text-sm text-gray-400 italic">No output entities</p>
                  )}
                </div>
              </div>
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