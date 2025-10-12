import React from 'react';
import { X, Folder, Database, BarChart3, Bot, Aperture, Zap, Brain } from 'lucide-react';
import { Tab, useTabContext } from '@/hooks/useTabContext';
import { UUID } from 'crypto';

interface CustomTabViewProps {
  children: React.ReactNode;
  projectId: UUID;
}

const TabView: React.FC<CustomTabViewProps> = ({ children, projectId }) => {
  const { openTabs, activeTabKey, selectTab, closeTabByKey } = useTabContext(projectId);
  
  const getTabIcon = (type: Tab['type']) => {
    switch (type) {
      case 'project':
        return <Aperture size={16} className="mr-2 text-gray-900" />;
      case 'data_source':
        return <Database size={16} className="mr-2 text-gray-900" />;
      case 'dataset':
        return <Folder size={16} className="mr-2 text-gray-900" />;
      case 'analysis':
        return <BarChart3 size={16} className="mr-2 text-gray-900" />;
      case 'automation':
        return <Bot size={16} className="mr-2 text-gray-900" />;
      case 'pipeline':
        return <Zap size={16} className="mr-2 text-gray-900" />;
      case 'model_entity':
        return <Brain size={16} className="mr-2 text-gray-900" />;
      default:
        return null;
    }
  };
  
  return (
    <div className="flex flex-col h-full w-full pt-10">
      <div className="flex items-center bg-gray-100 border-b border-gray-400 text-gray-900 h-14">
        {openTabs.map(tab => (
          <div
            key={tab.key}
            className={`text-sm flex items-center px-2 py-1 cursor-pointer h-full ${activeTabKey === tab.key ? 'bg-gray-400 font-semibold' : 'hover:bg-gray-200'}`}
            onClick={() => selectTab(tab.key)}
          >
            {getTabIcon(tab.type)}
            <span>{tab.label}</span>
            {tab.closable !== false && (
              <button
                className="ml-1 text-gray-200 hover:text-gray-50 focus:outline-none"
                onClick={e => {
                  e.stopPropagation();
                  closeTabByKey(tab.key);
                }}
                aria-label="Close tab"
              >
                {activeTabKey === tab.key && <X size={16} />}
              </button>
            )}
          </div>
        ))}
      </div>
      <div className="flex-1 overflow-auto bg-gray-950">{children}</div>
    </div>
  );
};

export default TabView; 