import { useState } from 'react';
import { SupportedSource } from "@/types/data-sources";
import AddDataSourceModal from "@/app/data-sources/_components/AddDataSourceModal";
import SourceTypeIcon from "@/app/data-sources/_components/SourceTypeIcon";

type sourceInfo = {
    available: boolean,
    name: string,
}

export const sourceTypes: Record<SupportedSource, sourceInfo> = {
    'file': { available: true, name: "File"},
    's3': { available: false, name: "AWS S3"},
    'azure': { available: false, name: "Azure"},
    'gcp': { available: false, name: "GCP"},
    'psql': { available: false, name: "PostgreSQL"},
    'mongodb': { available: false, name: "MongoDB"},
};


// Add Data Source Modal
export default function AddDataSourceMenu() {
  const [selectedSourceType, setSelectedSourceType] = useState<SupportedSource | null>(null);   


  return (
    <div className="relative rounded-lg w-full h-full flex flex-col overflow-hidden bg-white">

        {!selectedSourceType ? (
            // Source Type Selection Page
            <>
                <div className="relative flex items-center justify-between p-2 border-b border-gray-200 flex-shrink-0">
                    <div>
                    <h3 className="text-xs font-mono uppercase tracking-wider text-gray-600">Add New Data Source</h3>
                    <p className="text-sm text-gray-600 mt-1">
                        Connect your raw data sources.
                    </p>
                    </div>
                </div>


                <div className="flex-1 p-4 overflow-y-auto">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4">
                    {(Object.keys(sourceTypes) as SupportedSource[]).map((sourceType) => (
                    <button
                        key={sourceType}
                        type="button"
                        onClick={() => sourceTypes[sourceType].available ? setSelectedSourceType(sourceType) : null}
                        disabled={!sourceTypes[sourceType].available}
                        className={`flex flex-col items-center justify-center p-6 rounded-lg border-2 text-center transition-colors duration-150 h-32 relative overflow-hidden ${
                        sourceTypes[sourceType].available
                            ? 'border-gray-200 bg-gray-50 text-gray-600 hover:border-[#000034] hover:bg-gray-100 hover:text-[#000034]'
                            : 'border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed'
                        }`}
                        title={sourceTypes[sourceType].available ? `${sourceType} coming soon` : `${sourceType} coming soon`}
                    >
                            {SourceTypeIcon(sourceType, 32)}
                        <span className="text-sm font-medium mt-3">{sourceTypes[sourceType].name}</span>
                        {!sourceTypes[sourceType].available && (
                        <span className="absolute bottom-2 right-2 text-[10px] bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded">Coming Soon</span>
                        )}
                    </button>
                    ))}
                    </div>
                </div>
            </>
        ) : (
            <AddDataSourceModal isOpen={true} onClose={() => setSelectedSourceType(null)} selectedSourceType={selectedSourceType} setSelectedSourceType={setSelectedSourceType} />
        )}
    </div>  
  );
}