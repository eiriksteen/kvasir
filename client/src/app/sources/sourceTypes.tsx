import Image from 'next/image';
import { SupportedSource } from '@/types/data-integration';


// type sourceTypeObject = {
//     available: boolean,
//     icon: React.ReactNode,
// }

type sourceInfo = {
    available: boolean,
    icon: React.ReactNode,
}

export const sourceTypes: Record<SupportedSource, sourceInfo> = {
    File: { available: true, icon: <Image src="/file.svg" alt="File" width={32} height={32} /> },
    'AWS S3': { available: false, icon: <Image src="/s3.png" alt="AWS S3" width={32} height={32} /> },
    'Azure Blob': { available: false, icon: <Image src="/azure.png" alt="Azure Blob Storage" width={32} height={32} /> },
    'GCP Storage': { available: false, icon: <Image src="/gcloud.png" alt="Google Cloud Storage" width={128} height={128} /> },
    PostgreSQL: { available: false, icon: <Image src="/psql.png" alt="PostgreSQL Database" width={32} height={32} /> },
    MongoDB: { available: false, icon: <Image src="/mongodb.png" alt="MongoDB Database" width={128} height={128} /> },
};