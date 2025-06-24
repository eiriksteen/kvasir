import { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { AnalysisJobResultMetadata, AnalysisStep } from '@/types/analysis';
import { useContext } from '@/hooks/useContext';

interface AnalysisPlanViewProps {
  analysis: AnalysisJobResultMetadata;
}

const AnalysisPlanView = ({ analysis }: AnalysisPlanViewProps) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showSteps, setShowSteps] = useState(false);

  return (
    <div className="border-2 rounded-lg p-4 mb-4 bg-[#1a1625]/95 border-[#271a30] text-white">
      <div 
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div>
          <h3 className="text-lg font-medium text-purple-300">Analysis Plan</h3>
          <p className="text-sm text-zinc-400">
            Created: {new Date(analysis.createdAt).toLocaleString()}
          </p>
        </div>
        {isExpanded ? <ChevronDown size={20} className="text-purple-300" /> : <ChevronRight size={20} className="text-purple-300" />}
      </div>
      
      {isExpanded && (
        <div className="mt-4 space-y-4">
          <div className="bg-[#2a1c30] p-4 rounded-lg border border-purple-900/30">
            <h4 className="font-medium text-purple-300 mb-2">Overview</h4>
            <p className="text-zinc-300">
              {analysis.analysisPlan.analysisOverview}
            </p>
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="font-medium text-purple-300">Steps</h4>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowSteps(!showSteps);
                }}
                className="px-3 py-1 text-sm rounded-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white transition-all duration-200 shadow-sm hover:shadow-md"
              >
                {showSteps ? 'Hide Steps' : 'Show Steps'}
              </button>
            </div>
            {showSteps && (
              <div className="space-y-2 mt-2">
                {analysis.analysisPlan.analysisPlan.map((step: AnalysisStep, index: number) => (
                  <div 
                    key={index} 
                    className="bg-[#2a1c30] p-4 rounded-lg border border-purple-900/30"
                  >
                    <h5 className="font-medium text-purple-300">{step.stepName}</h5>
                    <p className="text-zinc-300 mt-1">
                      {step.stepDescription}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default function MainView() {
  const { analysisesInContext } = useContext();

  // Filter to only show analyses that are in the current context
  const analysesInContext = analysisesInContext?.filter((analysis: AnalysisJobResultMetadata) => 
    analysisesInContext.some((contextAnalysis: AnalysisJobResultMetadata) => contextAnalysis.jobId === analysis.jobId)
  );

  if (!analysesInContext || analysesInContext.length === 0) {
    return null;
  }

  return (
    <div className="p-4 bg-[#1a1625] min-h-screen mr-[400px]">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold mb-4 text-purple-300">Analysis Plans in Context</h2>
        <div className="h-[calc(100vh-8rem)] overflow-y-auto pr-4">
          <div className="space-y-4">
            {analysesInContext.map((analysis: AnalysisJobResultMetadata) => (
              <AnalysisPlanView key={analysis.jobId} analysis={analysis} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
