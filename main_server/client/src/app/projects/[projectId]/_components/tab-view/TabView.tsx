import React, { useRef, useEffect, useCallback } from 'react';
import { X, Folder, Database, BarChart3, Bot, Aperture, Zap, Brain, File } from 'lucide-react';
import { 
  SiPython, 
  SiJavascript, 
  SiTypescript, 
  SiReact,
  SiYaml,
  SiMarkdown,
  SiHtml5,
  SiCss3,
  SiShell,
} from 'react-icons/si';
import { VscJson, VscFile } from 'react-icons/vsc';
import { TabType, Tab } from '@/hooks/useTabs';
import { useProject } from '@/hooks/useProject';
import { useDatasets } from '@/hooks/useDatasets';
import { useDataSources } from '@/hooks/useDataSources';
import { useAnalyses } from '@/hooks/useAnalysis';
import { usePipelines } from '@/hooks/usePipelines';
import { useModelEntities } from '@/hooks/useModelEntities';
import { UUID } from 'crypto';

interface CustomTabViewProps {
  projectId: UUID;
  openTabs: Tab[];
  activeTabId: UUID | null | string;
  closeTab: (id: UUID | null | string) => void;
  selectTab: (id: UUID | null | string) => void;
}

const TabView: React.FC<CustomTabViewProps> = ({ 
  projectId, 
  openTabs, 
  activeTabId, 
  closeTab, 
  selectTab 
}) => {
  const { project } = useProject(projectId);
  const { datasets } = useDatasets(projectId);
  const { dataSources } = useDataSources(projectId);
  const { analysisObjects } = useAnalyses(projectId);
  const { pipelines } = usePipelines(projectId);
  const { modelsInstantiated } = useModelEntities(projectId);
  
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const codeScrollContainerRef = useRef<HTMLDivElement>(null);
  
  // Separate project tab, entity tabs, and code tabs
  const projectTab = openTabs.find(tab => tab.id === null);
  const otherTabs = openTabs.filter(tab => tab.id !== null);
  
  // Separate entity tabs from code tabs
  const entityTabs = otherTabs.filter(tab => !tab.filePath);
  const codeTabs = otherTabs.filter(tab => tab.filePath);
  
  // Determine if we need two rows
  const hasEntityTabs = entityTabs.length > 0;
  const hasCodeTabs = codeTabs.length > 0;
  const showTwoRows = hasEntityTabs && hasCodeTabs;
  
  // Auto-scroll to active tab
  const scrollToActiveTab = useCallback(() => {
    if (activeTabId) {
      // Try entity tabs container first
      if (scrollContainerRef.current) {
        const activeTabElement = scrollContainerRef.current.querySelector(`[data-tab-id="${activeTabId}"]`) as HTMLElement;
        if (activeTabElement) {
          const container = scrollContainerRef.current;
          const containerRect = container.getBoundingClientRect();
          const elementRect = activeTabElement.getBoundingClientRect();
          
          const scrollLeft = elementRect.left - containerRect.left + container.scrollLeft - (containerRect.width / 2) + (elementRect.width / 2);
          
          container.scrollTo({
            left: Math.max(0, scrollLeft),
            behavior: 'smooth'
          });
          return;
        }
      }
      
      // Try code tabs container
      if (codeScrollContainerRef.current) {
        const activeTabElement = codeScrollContainerRef.current.querySelector(`[data-tab-id="${activeTabId}"]`) as HTMLElement;
        if (activeTabElement) {
          const container = codeScrollContainerRef.current;
          const containerRect = container.getBoundingClientRect();
          const elementRect = activeTabElement.getBoundingClientRect();
          
          const scrollLeft = elementRect.left - containerRect.left + container.scrollLeft - (containerRect.width / 2) + (elementRect.width / 2);
          
          container.scrollTo({
            left: Math.max(0, scrollLeft),
            behavior: 'smooth'
          });
        }
      }
    }
  }, [activeTabId]);
  
  // Auto-scroll to active tab when it changes
  useEffect(() => {
    if (activeTabId && activeTabId !== null) {
      setTimeout(scrollToActiveTab, 150);
    }
  }, [activeTabId, scrollToActiveTab]);
  
  // Get file icon based on extension with brand colors
  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase();
    const size = 12;
    
    switch (ext) {
      case 'py':
        return <SiPython size={size} className="flex-shrink-0 text-[#3776AB]" />;
      case 'js':
        return <SiJavascript size={size} className="flex-shrink-0 text-[#F7DF1E]" />;
      case 'jsx':
        return <SiReact size={size} className="flex-shrink-0 text-[#61DAFB]" />;
      case 'ts':
        return <SiTypescript size={size} className="flex-shrink-0 text-[#3178C6]" />;
      case 'tsx':
        return <SiReact size={size} className="flex-shrink-0 text-[#3178C6]" />;
      case 'json':
        return <VscJson size={size} className="flex-shrink-0 text-[#6b7280]" />;
      case 'yaml':
      case 'yml':
        return <SiYaml size={size} className="flex-shrink-0 text-[#6b7280]" />;
      case 'md':
      case 'mdx':
        return <SiMarkdown size={size} className="flex-shrink-0 text-[#6b7280]" />;
      case 'html':
        return <SiHtml5 size={size} className="flex-shrink-0 text-[#E34F26]" />;
      case 'css':
        return <SiCss3 size={size} className="flex-shrink-0 text-[#1572B6]" />;
      case 'sh':
      case 'bash':
        return <SiShell size={size} className="flex-shrink-0 text-[#4EAA25]" />;
      case 'txt':
      case 'csv':
      case 'sql':
        return <VscFile size={size} className="flex-shrink-0 text-[#6b7280]" />;
      default:
        return <File size={12} className="flex-shrink-0 text-[#6b7280]" />;
    }
  };
  
  // Determine the type of a tab based on its ID
  const getTabType = (tab: Tab): TabType => {
    const id = tab.id;
    if (id === null) return 'project';
    
    if (project?.graph.dataSources.some(ds => ds.id === id)) return 'data_source';
    if (project?.graph.datasets.some(ds => ds.id === id)) return 'dataset';
    if (project?.graph.analyses.some(a => a.id === id)) return 'analysis';
    if (project?.graph.pipelines.some(p => p.id === id)) return 'pipeline';
    if (project?.graph.modelsInstantiated.some(m => m.id === id)) return 'model_instantiated';
    else return 'code';

  };
  
  // Get the label for a tab based on its ID and type
  const getTabLabel = (tab: Tab, type: TabType): string => {
    const id = tab.id;
    if (id === null) return ''; // Project tab has no label
    
    switch (type) {
      case 'code':
        // Extract just the filename from the full path
        return tab.filePath?.split('/').pop() || '';
      case 'data_source':
        return dataSources?.find(ds => ds.id === id)?.name || '';
      case 'dataset':
        return datasets?.find(ds => ds.id === id)?.name || '';
      case 'analysis':
        return analysisObjects?.find(a => a.id === id)?.name || '';
      case 'pipeline':
        return pipelines?.find(p => p.id === id)?.name || '';
      case 'model_instantiated':
        return modelsInstantiated?.find(m => m.id === id)?.name || '';
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
      case 'code':
        return {
          bg: 'bg-[#4a5568]/10',
          icon: 'text-[#4a5568]',
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
      case 'model_instantiated':
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
  
  const getTabIcon = (tab: Tab, type: TabType, isActive: boolean) => {
    const colors = getTabColor(type, isActive);
    const iconClass = `${colors.icon}`;
    
    switch (type) {
      case 'project':
        return <Aperture size={12} className={iconClass} />;
      case 'code':
        const fileName = tab.filePath?.split('/').pop() || '';
        return getFileIcon(fileName);
      case 'data_source':
        return <Database size={12} className={iconClass} />;
      case 'dataset':
        return <Folder size={12} className={iconClass} />;
      case 'analysis':
        return <BarChart3 size={12} className={iconClass} />;
      case 'automation':
        return <Bot size={12} className={iconClass} />;
      case 'pipeline':
        return <Zap size={12} className={iconClass} />;
      case 'model_instantiated':
        return <Brain size={12} className={iconClass} />;
      default:
        return null;
    }
  };
  
  // Individual tab component
  const TabComponent: React.FC<{ tab: Tab }> = ({ tab }) => {
    const type = getTabType(tab);
    const label = getTabLabel(tab, type);
    const isActive = activeTabId === tab.id;
    const colors = getTabColor(type, isActive);
    
    return (
      <div
        data-tab-id={tab.id}
        className={`font-mono text-xs flex items-center ${type !== 'project' ? 'gap-1.5' : ''} px-3 py-2 cursor-pointer h-full whitespace-nowrap ${
          isActive 
            ? colors.bg 
            : colors.hover
        }`}
        onClick={() => selectTab(tab.id)}
      >
        {getTabIcon(tab, type, isActive)}
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
    );
  };
  
  // Render a row of tabs
  const renderTabRow = (tabs: Tab[], scrollRef: React.RefObject<HTMLDivElement | null>) => (
    <div className="flex items-center flex-1 relative min-w-0">
      <div
        ref={scrollRef}
        className="flex items-center overflow-x-auto flex-1 min-w-0"
        style={{ 
          scrollbarWidth: 'none', 
          msOverflowStyle: 'none'
        }}
      >
        <style jsx>{`
          div::-webkit-scrollbar {
            display: none;
          }
        `}</style>
        {tabs.map((tab, index) => (
          <React.Fragment key={tab.id}>
            {index > 0 && <div className="h-full w-px bg-gray-300 flex-shrink-0" />}
            <div className="flex-shrink-0">
              <TabComponent tab={tab} />
            </div>
          </React.Fragment>
        ))}
      </div>
    </div>
  );

  return (
    <div className="mt-12">
      {/* First row: Project tab + Entity tabs (or code tabs if no entities) */}
      <div className="flex items-center bg-gray-100 border-b border-t border-gray-400 h-7">
        {/* Project tab - always visible */}
        <div className="flex items-center flex-shrink-0">
          <div className="h-full w-px bg-gray-300" />
          {projectTab ? (
            <TabComponent tab={projectTab} />
          ) : (
            <div className="font-mono text-xs flex items-center px-3 py-2 cursor-pointer h-full bg-[#000034] text-white">
              <Aperture size={12} className="text-white" />
            </div>
          )}
        </div>
        
        {/* Entity tabs or code tabs if no entities */}
        {(hasEntityTabs ? entityTabs : codeTabs).length > 0 && 
          renderTabRow(hasEntityTabs ? entityTabs : codeTabs, scrollContainerRef)
        }
      </div>
      
      {/* Second row: Code tabs (only if we have both entity and code tabs) */}
      {showTwoRows && (
        <div className="flex items-center bg-gray-100 border-b border-gray-300 h-7">
          <div className="flex items-center flex-shrink-0">
            <div className="h-full w-px bg-gray-300" />
          </div>
          
          {renderTabRow(codeTabs, codeScrollContainerRef)}
        </div>
      )}
    </div>
  );
};

export default TabView; 