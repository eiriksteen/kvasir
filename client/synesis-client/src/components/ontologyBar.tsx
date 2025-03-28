'use client';

import { useState, useMemo } from 'react';
import { Database, Plus, Check, Upload, Loader2 } from 'lucide-react';
import { TimeSeriesDataset } from '@/types/datasets';
import { Automation } from '@/types/automations';
import { useDatasets } from '@/hooks/apiHooks';
import { useSession } from 'next-auth/react';
import { redirect } from 'next/navigation';
import AddDataset from '@/components/addDataset';
// Props type
interface OntologyBarProps {
    datasetsInContext: TimeSeriesDataset[];
    automationsInContext: Automation[];
    onAddDatasetToContext: (dataset: TimeSeriesDataset) => void;
    onRemoveDatasetFromContext: (datasetId: string) => void;
    onAddAutomationToContext: (automation: Automation) => void;
    onRemoveAutomationFromContext: (automationId: string) => void;
    setIntegrationJobState: (jobState: string) => void;
}

function DatasetItem({ 
    dataset, 
    isInContext, 
    onClick 
}: { 
    dataset: TimeSeriesDataset; 
    isInContext: boolean; 
    onClick: () => void 
}) {
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
                        <span>timeseries</span>
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

function AutomationItem({ 
    automation, 
    isSelected, 
    onClick 
}: { 
    automation: Automation; 
    isSelected: boolean; 
    onClick: () => void 
}) {
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

export default function OntologyBar({ 
    datasetsInContext, 
    automationsInContext,
    onAddDatasetToContext, 
    onRemoveDatasetFromContext,
    onAddAutomationToContext,
    onRemoveAutomationFromContext,
    setIntegrationJobState
}: OntologyBarProps) {

    const [selectedAutomation, setSelectedAutomation] = useState<string | null>(null);
    const [showAutomations, setShowAutomations] = useState(false);
    const [showAddDataset, setShowAddDataset] = useState(false);
    const {data: session} = useSession();

    if (!session) {
        redirect("/login");
    }

    const { datasets } = useDatasets(session?.APIToken.accessToken);
    const automations: Automation[] = [];


    const filteredAutomations = useMemo(() => 
        datasetsInContext.length > 0
            ? automations.filter(automation => 
                datasetsInContext.some(dataset => automation.datasetIds.includes(dataset.id)))
            : automations,
        [datasetsInContext, automations]
    );

        
    const handleDatasetToggle = (dataset: TimeSeriesDataset) => {
        const isActive = datasetsInContext.some(d => d.id === dataset.id);
        if (isActive) {
            onRemoveDatasetFromContext(dataset.id);
        } else {
            onAddDatasetToContext(dataset);
        }
    };

    const isDatasetInContext = (datasetId: string) => 
        datasetsInContext.some(dataset => dataset.id === datasetId);
        

    return (
        <div className="relative flex pt-12 h-screen">
            {/* Main Bar with Datasets */}
            <div className="w-[20%] min-w-[300px] bg-gray-950 border-r border-[#101827] text-white p-4 flex flex-col">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-sm font-mono uppercase tracking-wider text-[#6b89c0]">Datasets</h2>
                    <button
                        onClick={() => setShowAutomations(!showAutomations)}
                        className="px-3 py-1 text-xs rounded-full text-white"
                    >
                        {showAutomations ? 'Hide Automations' : 'Show Automations'}
                    </button>
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
                    
                    <button
                        onClick={() => setShowAddDataset(true)}
                        className="w-full py-2 px-3 text-white rounded-md transition-colors flex items-center justify-center gap-2 text-sm border border-[#2a4170]"
                    >
                        <Upload size={14} />
                        <span>Add Dataset</span>
                    </button>
                </div>
            </div>

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

            {showAddDataset && (
                <AddDataset
                    isOpen={showAddDataset}
                    onClose={() => setShowAddDataset(false)}
                    onAdd={() => setIntegrationJobState("running")}
                />
            )}
        </div>
    );
}
