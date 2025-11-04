import { useCallback, useState } from 'react';
import { UUID } from 'crypto';

export type TabType = 'project' | 'data_source' | 'dataset' | 'analysis' | 'automation' | 'pipeline' | 'model_entity';

export interface Tab {
  id: UUID | null;  // null = project tab
  closable?: boolean;
  initialView?: 'overview' | 'code' | 'runs';  // For pipeline tabs
}

interface TabState {
  openTabs: Tab[];
  activeTabId: UUID | null;
}

// Default tab state
const getDefaultTabState = (): TabState => ({
  openTabs: [
    { id: null, closable: false }  // null = project tab
  ],
  activeTabId: null
});

export const useTabs = () => {
  const [tabState, setTabState] = useState<TabState>(getDefaultTabState());

  const openTab = useCallback((id: UUID | null, closable: boolean = true, initialView?: 'overview' | 'code' | 'runs') => {
    setTabState(current => {
      // If tab is already open, update its initialView and activate it
      const existingTabIndex = current.openTabs.findIndex(t => t.id === id);
      if (existingTabIndex !== -1) {
        const updatedTabs = [...current.openTabs];
        updatedTabs[existingTabIndex] = { 
          ...updatedTabs[existingTabIndex], 
          initialView 
        };
        return { 
          ...current, 
          openTabs: updatedTabs,
          activeTabId: id 
        };
      }
      
      // Add new tab
      return {
        ...current,
        openTabs: [...current.openTabs, { id, closable, initialView }],
        activeTabId: id
      };
    });
  }, []);

  const closeTab = useCallback((id: UUID | null) => {
    setTabState(current => {
      const filtered = current.openTabs.filter(tab => tab.id !== id);
      let newActiveTabId = current.activeTabId;
      
      // If closing the active tab, switch to the last tab (defaults to project tab)
      if (current.activeTabId === id) {
        newActiveTabId = filtered.length > 0 ? filtered[filtered.length - 1].id : null;
      }
      
      return {
        ...current,
        openTabs: filtered,
        activeTabId: newActiveTabId
      };
    });
  }, []);

  const closeTabToProject = useCallback(() => {
    setTabState(current => {
      return {
        ...current,
        activeTabId: null  // Always go back to project view
      };
    });
  }, []);

  const selectTab = useCallback((id: UUID | null) => {
    setTabState(current => ({ ...current, activeTabId: id }));
  }, []);

  return {
    openTabs: tabState.openTabs,
    activeTabId: tabState.activeTabId,
    openTab,
    closeTab,
    closeTabToProject,
    selectTab,
  };
};