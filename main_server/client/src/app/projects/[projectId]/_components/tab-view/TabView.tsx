import React from 'react';
import { X, Folder, Database, BarChart3, Bot, Aperture, Zap, Brain } from 'lucide-react';
import { TabType, useTabContext } from '@/hooks/useTabContext';
import { useProject } from '@/hooks/useProject';
import { useDatasets } from '@/hooks/useDatasets';
import { useDataSources } from '@/hooks/useDataSources';
import { useAnalyses } from '@/hooks/useAnalysis';
import { usePipelines } from '@/hooks/usePipelines';
import { useModelEntities } from '@/hooks/useModelEntities';
import { UUID } from 'crypto';

interface CustomTabViewProps {
  projectId: UUID;
}

const TabView: React.FC<CustomTabViewProps> = ({ projectId }) => {
  const { openTabs, activeTabId, selectTab, closeTab } = useTabContext(projectId);
  const { project } = useProject(projectId);
  const { datasets } = useDatasets(projectId);
  const { dataSources } = useDataSources();
  const { analysisObjects } = useAnalyses(projectId);
  const { pipelines } = usePipelines(projectId);
  const { modelEntities } = useModelEntities(projectId);
  
  // Determine the type of a tab based on its ID
  const getTabType = (id: UUID | null): TabType => {
    if (id === null) return 'project';
    
    if (project?.dataSources.some(ds => ds.dataSourceId === id)) return 'data_source';
    if (project?.datasets.some(ds => ds.datasetId === id)) return 'dataset';
    if (project?.analyses.some(a => a.analysisId === id)) return 'analysis';
    if (project?.pipelines.some(p => p.pipelineId === id)) return 'pipeline';
    if (project?.modelEntities.some(m => m.modelEntityId === id)) return 'model_entity';
    
    return 'project'; // fallback
  };
  
  // Get the label for a tab based on its ID and type
  const getTabLabel = (id: UUID | null, type: TabType): string => {
    if (id === null) return ''; // Project tab has no label
    
    switch (type) {
      case 'data_source':
        return dataSources?.find(ds => ds.id === id)?.name || '';
      case 'dataset':
        return datasets?.find(ds => ds.id === id)?.name || '';
      case 'analysis':
        return analysisObjects?.find(a => a.id === id)?.name || '';
      case 'pipeline':
        return pipelines?.find(p => p.id === id)?.name || '';
      case 'model_entity':
        return modelEntities?.find(m => m.id === id)?.name || '';
      default:
        return '';
    }
  };
  
  const getTabColor = (type: TabType, isActive: boolean) => {
    switch (type) {
      case 'project':
        return {
          bg: isActive ? 'bg-[#000034]' : 'bg-gray-200',
          icon: isActive ? 'text-white' : 'text-[#000034]',
          hover: 'hover:bg-gray-200'
        };
      case 'data_source':
        return {
          bg: 'bg-[#6b7280]/10',
          icon: 'text-[#6b7280]',
          hover: 'hover:bg-gray-200'
        };
      case 'dataset':
        return {
          bg: 'bg-[#0E4F70]/10',
          icon: 'text-[#0E4F70]',
          hover: 'hover:bg-gray-200'
        };
      case 'analysis':
        return {
          bg: 'bg-[#004806]/10',
          icon: 'text-[#004806]',
          hover: 'hover:bg-gray-200'
        };
      case 'automation':
        return {
          bg: 'bg-[#0891b2]/10',
          icon: 'text-[#0891b2]',
          hover: 'hover:bg-gray-200'
        };
      case 'pipeline':
        return {
          bg: 'bg-[#840B08]/10',
          icon: 'text-[#840B08]',
          hover: 'hover:bg-gray-200'
        };
      case 'model_entity':
        return {
          bg: 'bg-[#491A32]/10',
          icon: 'text-[#491A32]',
          hover: 'hover:bg-gray-200'
        };
      default:
        return {
          bg: 'bg-gray-300/10',
          icon: 'text-gray-800',
          hover: 'hover:bg-gray-200'
        };
    }
  };
  
  const getTabIcon = (type: TabType, isActive: boolean) => {
    const colors = getTabColor(type, isActive);
    const iconClass = `${colors.icon}`;
    
    switch (type) {
      case 'project':
        return <Aperture size={14} className={iconClass} />;
      case 'data_source':
        return <Database size={14} className={iconClass} />;
      case 'dataset':
        return <Folder size={14} className={iconClass} />;
      case 'analysis':
        return <BarChart3 size={14} className={iconClass} />;
      case 'automation':
        return <Bot size={14} className={iconClass} />;
      case 'pipeline':
        return <Zap size={14} className={iconClass} />;
      case 'model_entity':
        return <Brain size={14} className={iconClass} />;
      default:
        return null;
    }
  };
  
  return (
    <div className="flex items-center bg-gray-100 border-b border-t border-gray-400 h-9 mt-12">
      {openTabs.map((tab, index) => {
        const type = getTabType(tab.id);
        const label = getTabLabel(tab.id, type);
        const isActive = activeTabId === tab.id;
        const colors = getTabColor(type, isActive);
        
        return (
          <React.Fragment key={tab.id ?? 'project'}>
            {index > 0 && (
              <div className="h-full w-px bg-gray-300" />
            )}
            <div
              className={`font-mono text-xs flex items-center ${type !== 'project' ? 'gap-1.5' : ''} px-3 py-3 cursor-pointer h-full ${
                isActive 
                  ? colors.bg 
                  : colors.hover
              }`}
              onClick={() => selectTab(tab.id)}
            >
              {getTabIcon(type, isActive)}
              <span className={isActive && type === 'project' ? 'text-white' : 'text-gray-800'}>{label}</span>
              {tab.closable !== false && (
                <button
                  className={`focus:outline-none ${
                    isActive && type === 'project' 
                      ? 'text-gray-300 hover:text-white' 
                      : 'text-gray-500 hover:text-gray-800'
                  }`}
                  onClick={e => {
                    e.stopPropagation();
                    closeTab(tab.id);
                  }}
                  aria-label="Close tab"
                >
                  <X size={12} />
                </button>
              )}
            </div>
          </React.Fragment>
        );
      })}
    </div>
  );
};

export default TabView; 