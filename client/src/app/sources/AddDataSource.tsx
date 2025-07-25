import { useState } from 'react';
import { SupportedSource } from "@/types/data-integration";
import AddDataSourceModal from "./AddDataSourceModal";
import { sourceTypes } from './sourceTypes';


// Add Data Source Modal
export default function AddDataSource() {
  const [selectedSourceType, setSelectedSourceType] = useState<SupportedSource | null>(null);   


  return (
    <div className="relative rounded-xl w-full max-w-6xl h-full max-h-[90vh] flex flex-col overflow-hidden shadow-2xl">

        {!selectedSourceType ? (
            // Source Type Selection Page
            <>
                <div className="relative flex items-center justify-between p-2 border-b border-[#101827] flex-shrink-0">
                    <div>
                    <h3 className="text-xs font-mono uppercase tracking-wider text-gray-400">Add New Data Source</h3>
                    <p className="text-sm text-gray-500 mt-1">
                        Connect your raw data sources.
                    </p>
                    </div>
                </div>

                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4">
                    {(Object.keys(sourceTypes) as SupportedSource[]).map((sourceType) => (
                    <button
                        key={sourceType}
                        type="button"
                        onClick={() => sourceTypes[sourceType].available ? setSelectedSourceType(sourceType) : null}
                        disabled={!sourceTypes[sourceType].available}
                        className={`flex flex-col items-center justify-center p-6 rounded-lg border-2 text-center transition-colors duration-150 h-32 relative overflow-hidden ${
                        sourceTypes[sourceType].available
                            ? 'border-zinc-700 bg-[#0a101c]/50 text-zinc-400 hover:border-zinc-600 hover:bg-[#0a101c] hover:text-zinc-300'
                            : 'border-zinc-800 bg-[#050a14]/30 text-zinc-600 cursor-not-allowed'
                        }`}
                        title={sourceTypes[sourceType].available ? `${sourceType} coming soon` : `${sourceType} coming soon`}
                    >
                            {sourceTypes[sourceType].icon}
                        <span className="text-sm font-medium mt-3">{sourceType}</span>
                        {!sourceTypes[sourceType].available && (
                        <span className="absolute bottom-2 right-2 text-[10px] bg-zinc-700 text-zinc-400 px-1.5 py-0.5 rounded">Coming Soon</span>
                        )}
                    </button>
                    ))}
                </div>
            </>
        ) : (
            <AddDataSourceModal isOpen={true} onClose={() => setSelectedSourceType(null)} selectedSourceType={selectedSourceType} setSelectedSourceType={setSelectedSourceType} />
        )}
    </div>  
  );
}