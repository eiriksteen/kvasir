'use client';

import { useState, useMemo } from 'react';
import { Database, Plus, Check } from 'lucide-react';
import { TimeSeriesDataset } from '@/types/datasets';
import { Automation } from '@/types/automations';
import { useAgentContext, useDatasets, useAnalysis } from '@/hooks';
import { useSession } from 'next-auth/react';
import { redirect } from 'next/navigation';
import { AnalysisJobResultMetadata } from '@/types/analysis';


function DatasetItem({ dataset, isInContext, onClick }: { dataset: TimeSeriesDataset; isInContext: boolean; onClick: () => void }) {
    return (
        <div
            onClick={onClick}
            className={`p-3 rounded-lg cursor-pointer transition-all duration-200 hover:bg-[#0a101c] border-2 ${
                isInContext ? 'bg-[#0a101c] border-[#2a4170]' : 'bg-[#050a14] border-[#101827]'
            }`}
        >
            <div className="flex justify-between items-center pr-2">
                <div className="flex-1">
                    <div className="text-sm font-medium">{dataset.name}</div>
                    <div className="text-xs text-zinc-400 flex items-center gap-1.5">
                        <span>Time Series</span>
                        {isInContext && (
                            <span className="bg-[#0e1a30] text-blue-300 text-xs px-1.5 py-0.5 rounded-full flex items-center gap-0.5">
                                <Database size={10} />
                            </span>
                        )}
                    </div>
                </div>
                
                <button 
                    onClick={(e) => {
                        e.stopPropagation(); // Prevent parent click
                        onClick();
                    }}
                    className={`p-1.5 rounded-full border shadow-md ${
                        isInContext
                            ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white border-blue-500 shadow-blue-900/30'
                            : 'bg-gradient-to-r from-[#1a2438] to-[#273349] text-blue-300 hover:text-white hover:from-blue-600 hover:to-blue-700 border-[#2a4170]'
                    }`}
                    title={isInContext ? "Remove from context" : "Add to chat context"}
                >
                    {isInContext ? <Check size={14} /> : <Plus size={14} />}
                </button>
            </div>
        </div>
    );
}

function AutomationItem({ automation, isSelected, onClick }: { automation: Automation; isSelected: boolean; onClick: () => void }) {
    return (
        <div
            onClick={onClick}
            className={`p-3 rounded-lg cursor-pointer hover:bg-[#2a1c30] border-2 ${
                isSelected ? 'bg-[#2a1c30] border-purple-800' : 'bg-[#1a1625]/80 border-[#271a30]'
            }`}
        >
            <div className="text-sm font-medium">{automation.name}</div>
            <div className="text-xs text-zinc-400">{automation.description}</div>
        </div>
    );
}

function AnalysisItem({ analysis, isSelected, onClick }: {analysis: AnalysisJobResultMetadata, isSelected: boolean, onClick: () => void }) {
    return (
        <div 
            onClick={onClick}
            className={`p-3 rounded-lg cursor-pointer hover:bg-[#1a2438] border-2 ${
                isSelected ? 'bg-[#1a2438] border-blue-800' : 'bg-[#0e1a30]/80 border-[#1a2438]'
            }`}
        >
            <div className="flex justify-between items-start">
                <div className="flex flex-col gap-2">
                    <div className="text-sm font-medium text-blue-300">Analysis Results</div>
                    <div className="text-xs text-zinc-400">
                        <div>Job ID: {analysis.jobId}</div>
                        <div>Datasets: {analysis.numberOfDatasets}</div>
                        <div>Automations: {analysis.numberOfAutomations}</div>
                        <div>Created: {new Date(analysis.createdAt).toLocaleDateString()}</div>
                        <div>PDF Created: {analysis.pdfCreated ? "Yes" : "No"}</div>
                    </div>
                </div>
                <button 
                    onClick={(e) => {
                        e.stopPropagation();
                        onClick();
                    }}
                    className={`p-1.5 rounded-full border shadow-md ${
                        isSelected
                            ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white border-blue-500 shadow-blue-900/30'
                            : 'bg-gradient-to-r from-[#1a2438] to-[#273349] text-blue-300 hover:text-white hover:from-blue-600 hover:to-blue-700 border-[#2a4170]'
                    }`}
                    title={isSelected ? "Remove from context" : "Add to chat context"}
                >
                    {isSelected ? <Check size={14} /> : <Plus size={14} />}
                </button>
            </div>
        </div>
    );
}

export default function OntologyBar() {
    const [selectedAutomation, setSelectedAutomation] = useState<string | null>(null);
    const [showAutomations, setShowAutomations] = useState(false);
    const [showAnalysis, setShowAnalysis] = useState(false);
    const [showAddDataset, setShowAddDataset] = useState(false);
    const {data: session} = useSession();
    const { 
        datasetsInContext, 
        addDatasetToContext, 
        removeDatasetFromContext,
        analysisesInContext,
        addAnalysisToContext,
        removeAnalysisFromContext
    } = useAgentContext();

    if (!session) {
        redirect("/login");
    }


    const { datasets } = useDatasets();
    const automations: Automation[] = [];
    const { analysisJobResults } = useAnalysis();
    console.log(analysisJobResults);


    const filteredAutomations = useMemo(() => 
        datasetsInContext.timeSeries.length > 0
            ? automations.filter((automation: Automation) => 
                datasetsInContext.timeSeries.some((dataset: TimeSeriesDataset) => automation.datasetIds.includes(dataset.id)))
            : automations,
        [datasetsInContext, automations]
    );

        
    const handleDatasetToggle = (dataset: TimeSeriesDataset) => {
        const isActive = datasetsInContext.timeSeries.some((d: TimeSeriesDataset) => d.id === dataset.id);
        if (isActive) {
            removeDatasetFromContext(dataset);
        } else {
            addDatasetToContext(dataset);
        }
    };


    const isDatasetInContext = (datasetId: string) => 
        datasetsInContext.timeSeries.some((dataset: TimeSeriesDataset) => dataset.id === datasetId);

    const handleAnalysisToggle = (analysis: AnalysisJobResultMetadata) => {
        const isActive = analysisesInContext.some((a: AnalysisJobResultMetadata) => a.jobId === analysis.jobId);
        if (isActive) {
            removeAnalysisFromContext(analysis);
        } else {
            addAnalysisToContext(analysis);
        }
    };

    return (
        <div className="relative flex pt-12 h-screen">
            {/* Main Bar with Datasets */}
            <div className="w-[300px] bg-gray-950 border-r border-[#101827] text-white p-4 flex flex-col">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-sm font-mono uppercase tracking-wider text-[#6b89c0]">Datasets</h2>
                    <div className="flex gap-2">
                        <button
                            onClick={() => setShowAnalysis(!showAnalysis)}
                            className="px-3 py-1 text-xs rounded-full text-white"
                        >
                            {showAnalysis ? 'Hide Analysis' : 'Show Analysis'}
                        </button>
                        <button
                            onClick={() => setShowAutomations(!showAutomations)}
                            className="px-3 py-1 text-xs rounded-full text-white"
                        >
                            {showAutomations ? 'Hide Automations' : 'Show Automations'}
                        </button>
                    </div>
                </div>
                
                <div className="space-y-2 flex-grow overflow-y-auto">
                    {datasets?.timeSeries.length === 0 && (
                        <div className="p-3 rounded-lg mb-3">
                            <p className="text-xs text-zinc-400">
                                No datasets found. 
                            </p>
                        </div>
                    )}
                    {datasets?.timeSeries.map((dataset) => (
                        <DatasetItem 
                            key={dataset.id}
                            dataset={dataset}
                            isInContext={isDatasetInContext(dataset.id)}
                            onClick={() => handleDatasetToggle(dataset)}
                        />
                    ))}
                    
                </div>
                
                {/* Footer section */}
                <div className="mt-4">
                    <div className="p-3 rounded-lg bg-[#111827] border border-[#1a2438] mb-3">
                        <h3 className="text-xs font-medium text-[#6b89c0] mb-2">Working with Datasets</h3>
                        <p className="text-xs text-zinc-400">
                            Click on a dataset to add it to the chat context. You can then ask for analysis or automation based on the selected datasets.
                        </p>
                    </div>
                </div>
            </div>

            {/* Analysis Side Panel */}
            {showAnalysis && (
                <div className="absolute left-[300px] top-12 w-[300px] h-[calc(100vh-3rem)] bg-[#1a1625]/95 text-white p-4 border-r border-purple-900/30">
                    <h2 className="text-sm font-mono uppercase tracking-wider text-purple-300 mb-4">Analysis</h2>
                    
                    <div className="space-y-2 flex-grow overflow-y-auto">
                        {analysisJobResults?.analysisJobResults.length === 0 && (    
                            <div className="p-3 rounded-lg mb-3">
                                <p className="text-xs text-zinc-400">
                                    No analysis found. 
                                </p>
                            </div>
                        )}
                        {analysisJobResults?.analysisJobResults.map((analysis: AnalysisJobResultMetadata) => (
                            <AnalysisItem
                                key={analysis.jobId}
                                analysis={analysis}
                                isSelected={analysisesInContext.some((a: AnalysisJobResultMetadata) => a.jobId === analysis.jobId)}
                                onClick={() => handleAnalysisToggle(analysis)}
                            />
                        ))}
                    </div>
                </div>
            )}

            {/* Automations Side Panel */}
            {showAutomations && (
                <div className="absolute left-[300px] top-12 w-[300px] h-[calc(100vh-3rem)] bg-[#1a1625]/95 text-white p-4 border-r border-purple-900/30">
                    <h2 className="text-sm font-mono uppercase tracking-wider text-purple-300 mb-4">Automations</h2>
                    <div className="space-y-2">
                        {filteredAutomations.length === 0 && (
                            <div className="p-3 rounded-lg mb-3">
                                <p className="text-xs text-zinc-400">
                                    No automations found.
                                </p>
                            </div>
                        )}
                        {filteredAutomations.map((automation) => (
                            <AutomationItem
                                key={automation.id}
                                automation={automation}
                                isSelected={selectedAutomation === automation.id}
                                onClick={() => setSelectedAutomation(
                                    selectedAutomation === automation.id ? null : automation.id
                                )}
                            />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
