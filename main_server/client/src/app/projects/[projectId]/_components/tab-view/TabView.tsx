import React from 'react';
import { X, Folder, Database, BarChart3, Bot, Aperture, Zap, Brain } from 'lucide-react';
import { Tab, useTabContext } from '@/hooks/useTabContext';
import { UUID } from 'crypto';

interface CustomTabViewProps {
  projectId: UUID;
}

const TabView: React.FC<CustomTabViewProps> = ({ projectId }) => {
  const { openTabs, activeTabKey, selectTab, closeTabByKey } = useTabContext(projectId);
  
  const getTabColor = (type: Tab['type'], isActive: boolean) => {
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
  
  const getTabIcon = (type: Tab['type'], isActive: boolean) => {
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
        const isActive = activeTabKey === tab.key;
        const colors = getTabColor(tab.type, isActive);
        
        return (
          <React.Fragment key={tab.key}>
            {index > 0 && (
              <div className="h-full w-px bg-gray-300" />
            )}
            <div
              className={`font-mono text-xs flex items-center ${tab.type !== 'project' ? 'gap-1.5' : ''} px-3 py-3 cursor-pointer h-full ${
                isActive 
                  ? colors.bg 
                  : colors.hover
              }`}
              onClick={() => selectTab(tab.key)}
            >
              {getTabIcon(tab.type, isActive)}
              <span className={isActive && tab.type === 'project' ? 'text-white' : 'text-gray-800'}>{tab.label}</span>
              {tab.closable !== false && (
                <button
                  className={`focus:outline-none ${
                    isActive && tab.type === 'project' 
                      ? 'text-gray-300 hover:text-white' 
                      : 'text-gray-500 hover:text-gray-800'
                  }`}
                  onClick={e => {
                    e.stopPropagation();
                    closeTabByKey(tab.key);
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