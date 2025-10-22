import { SupportedSource } from '@/types/data-sources';
import { FileSpreadsheet, FileJson } from 'lucide-react';


// type sourceTypeObject = {
//     available: boolean,
//     icon: React.ReactNode,
// }

type sourceInfo = {
    available: boolean,
}

export const sourceTypes: Record<SupportedSource, sourceInfo> = {
    'tabular_file': { available: true},
    'key_value_file': { available: true},
};

export default function SourceTypeIcon(sourceType: SupportedSource, size: number) {
    switch (sourceType) {
        case 'tabular_file':
            return <FileSpreadsheet size={size} className="text-gray-600" />;
        case 'key_value_file':
            return <FileJson size={size} className="text-gray-600" />;
    }
}