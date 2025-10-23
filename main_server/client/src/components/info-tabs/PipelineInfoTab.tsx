import { useEffect, useState, useMemo } from 'react';
import { UUID } from 'crypto';
import { usePipeline } from '@/hooks/usePipelines';
import { useRuns } from '@/hooks/useRuns';
import { useDatasets } from '@/hooks/useDatasets';
import { useProjectDataSources } from '@/hooks/useDataSources';
import { useModelEntities } from '@/hooks/useModelEntities';
import { useAnalyses } from '@/hooks/useAnalysis';
import { SquarePlay, FileCode, ArrowDownToLine, ArrowUpFromLine, Database, Folder, Brain, BarChart3, Info } from 'lucide-react';
import CodeStream from '@/components/code/CodeStream';
import CodeImplementation from '@/components/code/CodeImplementation';
import { Dataset } from '@/types/data-objects';
import { DataSource } from '@/types/data-sources';
import { ModelEntity } from '@/types/model';
import { AnalysisObjectSmall } from '@/types/analysis';
import { Run } from '@/types/runs';
import { mutate } from 'swr';

interface PipelineInfoTabProps {
  pipelineId: UUID;
  projectId: UUID;
  onClose: () => void;
}   

type ViewType = 'overview' | 'code' | 'runs';

export default function PipelineInfoTab({ 
  pipelineId,
  projectId,
  onClose
}: PipelineInfoTabProps) {

  const { pipeline } = usePipeline(pipelineId, projectId);
  const { runs } = useRuns();
  const { datasets } = useDatasets(projectId);
  const { dataSources } = useProjectDataSources(projectId);
  const { modelEntities } = useModelEntities(projectId);
  const { analysisObjects } = useAnalyses(projectId);
  
  const isInProgress = !pipeline?.implementation;
  const [currentView, setCurrentView] = useState<ViewType>(isInProgress ? 'code' : 'overview');

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
      <div className="flex gap-2 px-4 py-4">
        {!isInProgress && (
          <button
            onClick={() => setCurrentView('overview')}
            className={`flex items-center gap-2 px-4 py-0 rounded-lg transition-all ${
              currentView === 'overview'
                ? 'bg-[#840B08] text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <Info className="w-4 h-4" />
            <span className="text-sm font-medium">Overview</span>
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
              <CodeImplementation scriptId={pipeline.implementation.implementationScript.id} />
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
            {/* Description */}
            {pipeline.description ? (
              <p className="text-sm text-gray-700">
                {pipeline.description}
              </p>
            ) : (
              <p className="text-sm text-gray-400 italic">No description provided</p>
            )}
            {/* Inputs Box */}
            <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-[#840B08]/20 rounded-lg">
                  <ArrowDownToLine className="w-4 h-4 text-[#840B08]" />
                </div>
                <h3 className="text-sm font-semibold text-gray-900">Inputs</h3>
              </div>

              <div className="space-y-4">
                {/* Args */}
                {pipeline.implementation?.args && Object.keys(pipeline.implementation.args).length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-700 mb-2">Arguments</h4>
                    <div className="bg-white rounded-lg p-3 border border-gray-200">
                      <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                        {JSON.stringify(pipeline.implementation.args, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Input Entities */}
                <div>
                  <h4 className="text-xs font-semibold text-gray-700 mb-2">Input Entities</h4>
                  <div className="flex flex-wrap gap-1">
                    {pipeline.inputs.dataSourceIds.map((dataSourceId) => (
                      <div
                        key={dataSourceId}
                        className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-gray-200 text-gray-600"
                      >
                        <Database size={12} />
                        {dataSources?.find((ds: DataSource) => ds.id === dataSourceId)?.name || 'Data Source'}
                      </div>
                    ))}
                    {pipeline.inputs.datasetIds.map((datasetId) => (
                      <div
                        key={datasetId}
                        className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-[#0E4F70]/20 text-[#0E4F70]"
                      >
                        <Folder size={12} />
                        {datasets?.find((ds: Dataset) => ds.id === datasetId)?.name || 'Dataset'}
                      </div>
                    ))}
                    {pipeline.inputs.modelEntityIds.map((modelEntityId) => (
                      <div
                        key={modelEntityId}
                        className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-[#491A32]/20 text-[#491A32]"
                      >
                        <Brain size={12} />
                        {modelEntities?.find((me: ModelEntity) => me.id === modelEntityId)?.name || 'Model'}
                      </div>
                    ))}
                    {pipeline.inputs.analysisIds.map((analysisId) => (
                      <div
                        key={analysisId}
                        className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-[#004806]/20 text-[#004806]"
                      >
                        <BarChart3 size={12} />
                        {analysisObjects?.find((a: AnalysisObjectSmall) => a.id === analysisId)?.name || 'Analysis'}
                      </div>
                    ))}
                    {pipeline.inputs.dataSourceIds.length === 0 &&
                     pipeline.inputs.datasetIds.length === 0 &&
                     pipeline.inputs.modelEntityIds.length === 0 &&
                     pipeline.inputs.analysisIds.length === 0 && (
                      <p className="text-xs text-gray-500 italic">No input entities</p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Outputs Box */}
            <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-[#840B08]/20 rounded-lg">
                  <ArrowUpFromLine className="w-4 h-4 text-[#840B08]" />
                </div>
                <h3 className="text-sm font-semibold text-gray-900">Outputs</h3>
              </div>

              <div className="space-y-4">
                {/* Output Variables Schema */}
                {pipeline.implementation?.outputVariablesSchema && Object.keys(pipeline.implementation.outputVariablesSchema).length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-gray-700 mb-2">Output Variables Schema</h4>
                    <div className="bg-white rounded-lg p-3 border border-gray-200">
                      <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                        {JSON.stringify(pipeline.implementation.outputVariablesSchema, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Output Entities */}
                <div>
                  <h4 className="text-xs font-semibold text-gray-700 mb-2">Output Entities</h4>
                  <div className="flex flex-wrap gap-1">
                    {pipeline.outputs.datasetIds.map((datasetId) => (
                      <div
                        key={datasetId}
                        className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-[#0E4F70]/20 text-[#0E4F70]"
                      >
                        <Folder size={12} />
                        {datasets?.find((ds: Dataset) => ds.id === datasetId)?.name || 'Dataset'}
                      </div>
                    ))}
                    {pipeline.outputs.modelEntityIds.map((modelEntityId) => (
                      <div
                        key={modelEntityId}
                        className="px-2 py-1 text-xs rounded-full flex items-center gap-1 bg-[#491A32]/20 text-[#491A32]"
                      >
                        <Brain size={12} />
                        {modelEntities?.find((me: ModelEntity) => me.id === modelEntityId)?.name || 'Model'}
                      </div>
                    ))}
                    {pipeline.outputs.datasetIds.length === 0 &&
                     pipeline.outputs.modelEntityIds.length === 0 && (
                      <p className="text-xs text-gray-500 italic">No output entities</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}