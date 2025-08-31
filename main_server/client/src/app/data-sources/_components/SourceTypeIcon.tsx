import Image from 'next/image';
import { SupportedSource } from '@/types/data-sources';


// type sourceTypeObject = {
//     available: boolean,
//     icon: React.ReactNode,
// }

type sourceInfo = {
    available: boolean,
}

export const sourceTypes: Record<SupportedSource, sourceInfo> = {
    'TabularFile': { available: true},
    'AWS S3': { available: false},
    'Azure Blob': { available: false},
    'GCP Storage': { available: false},
    'PostgreSQL': { available: false},
    'MongoDB': { available: false},
};

export default function SourceTypeIcon(sourceType: SupportedSource, size: number) {
    switch (sourceType) {
        case 'TabularFile':
            return <Image src="/file.svg" alt="File" width={size} height={size} />;
        case 'AWS S3':
            return <Image src="/s3.png" alt="AWS S3" width={size} height={size} />;
        case 'Azure Blob':
            return <Image src="/azure.png" alt="Azure Blob Storage" width={size} height={size} />;
        case 'GCP Storage':
            return <Image src="/gcloud.png" alt="Google Cloud Storage" width={size} height={size} />;
        case 'PostgreSQL':
            return <Image src="/psql.png" alt="PostgreSQL Database" width={size} height={size} />;
        case 'MongoDB':
            return <Image src="/MongoDB.svg" alt="MongoDB Database" width={size} height={size} />;
    }
}