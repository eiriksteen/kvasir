import { SupportedSource } from '@/types/data-integration';
import { FolderOpen, Database } from 'lucide-react';    


// Component for source type icon with color coding
export default function SourceTypeIcon({ type, size = 16 }: { type: SupportedSource; size?: number }) {
  const getIconAndColor = (type: SupportedSource) => {
    switch (type) {
      case 'file':
        return {
          icon: <FolderOpen size={size} />,
          color: 'text-green-400',
          bgColor: 'bg-green-500/10',
          borderColor: 'border-green-500/20'
        };
      case 'aws_s3':
        return {
          icon: <Database size={size} />,
          color: 'text-orange-400',
          bgColor: 'bg-orange-500/10',
          borderColor: 'border-orange-500/20'
        };
      case 'azure_blob':
        return {
          icon: <Database size={size} />,
          color: 'text-blue-400',
          bgColor: 'bg-blue-500/10',
          borderColor: 'border-blue-500/20'
        };
      case 'gcp_storage':
        return {
          icon: <Database size={size} />,
          color: 'text-red-400',
          bgColor: 'bg-red-500/10',
          borderColor: 'border-red-500/20'
        };
      case 'postgresql':
        return {
          icon: <Database size={size} />,
          color: 'text-indigo-400',
          bgColor: 'bg-indigo-500/10',
          borderColor: 'border-indigo-500/20'
        };
      case 'mongodb':
        return {
          icon: <Database size={size} />,
          color: 'text-emerald-400',
          bgColor: 'bg-emerald-500/10',
          borderColor: 'border-emerald-500/20'
        };
      default:
        return {
          icon: <Database size={size} />,
          color: 'text-gray-400',
          bgColor: 'bg-gray-500/10',
          borderColor: 'border-gray-500/20'
        };
    }
  };

  const { icon, color, bgColor, borderColor } = getIconAndColor(type);
  
  return (
    <div className={`p-2 rounded-md ${bgColor} border ${borderColor}`}>
      <div className={color}>
        {icon}
      </div>
    </div>
  );
}