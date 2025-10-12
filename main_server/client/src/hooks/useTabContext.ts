import { useCallback, useRef } from 'react';
import useSWR from 'swr';
import { UUID } from 'crypto';

export type TabType = 'project' | 'data_source' | 'dataset' | 'analysis' | 'automation' | 'pipeline' | 'model_entity';

export interface Tab {
  key: string;
  label: string;
  type: TabType;
  id: string;
  closable?: boolean;
}

interface TabState {
  openTabs: Tab[];
  activeTabKey: string;
}

// Default tab state
const getDefaultTabState = (projectId: UUID): TabState => ({
  openTabs: [
    { key: 'project', label: '', type: 'project', id: projectId, closable: false }
  ],
  activeTabKey: 'project'
});

export const useTabContext = (projectId: UUID) => {
  // Use a ref to store the current tab state to prevent SWR from resetting it
  const tabStateRef = useRef<TabState>(getDefaultTabState(projectId));
  
  const { data: tabState, mutate: mutateTabState } = useSWR(
    `tabs-${projectId}`,
    () => tabStateRef.current, // Return the current state instead of default
    {
      fallbackData: getDefaultTabState(projectId),
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      revalidateOnMount: false, // Prevent revalidation on mount
      revalidateIfStale: false, // Prevent revalidation if stale
    }
  );

  const openTab = useCallback((tab: Omit<Tab, 'key'>) => {
    const key = `${tab.type}-${tab.id}`;
    mutateTabState((current: TabState | undefined) => {
      if (!current) {
        const defaultState = getDefaultTabState(projectId);
        tabStateRef.current = defaultState;
        return defaultState;
      }
      
      if (current.openTabs.some(t => t.key === key)) {
        const newState = { ...current, activeTabKey: key };
        tabStateRef.current = newState;
        return newState;
      }
      
      const newState = {
        ...current,
        openTabs: [...current.openTabs, { ...tab, key }],
        activeTabKey: key
      };
      tabStateRef.current = newState;
      return newState;
    }, { revalidate: false });
  }, [projectId, mutateTabState]);

  const closeTab = useCallback((entityId: string, entityType: TabType) => {
    const key = `${entityType}-${entityId}`;
    closeTabByKey(key);
  }, []);

  const closeTabByKey = useCallback((key: string) => {
    mutateTabState((current: TabState | undefined) => {
      if (!current) {
        const defaultState = getDefaultTabState(projectId);
        tabStateRef.current = defaultState;
        return defaultState;
      }
      
      const filtered = current.openTabs.filter(tab => tab.key !== key);
      let newActiveTabKey = current.activeTabKey;
      
      // If closing the active tab, switch to the last tab (never closes project tab)
      if (current.activeTabKey === key) {
        newActiveTabKey = filtered.length > 0 ? filtered[filtered.length - 1].key : 'project';
      }
      
      const newState = {
        ...current,
        openTabs: filtered,
        activeTabKey: newActiveTabKey
      };
      tabStateRef.current = newState;
      return newState;
    }, { revalidate: false });
  }, [projectId, mutateTabState]);

  const selectTab = useCallback((key: string) => {
    mutateTabState((current: TabState | undefined) => {
      if (!current) {
        const defaultState = getDefaultTabState(projectId);
        tabStateRef.current = defaultState;
        return defaultState;
      }
      const newState = { ...current, activeTabKey: key };
      tabStateRef.current = newState;
      return newState;
    }, { revalidate: false });
  }, [projectId, mutateTabState]);

  const setProjectTabLabel = useCallback((label: string) => {
    mutateTabState((current: TabState | undefined) => {
      if (!current) {
        const defaultState = getDefaultTabState(projectId);
        tabStateRef.current = defaultState;
        return defaultState;
      }
      
      const newState = {
        ...current,
        openTabs: current.openTabs.map(tab =>
          tab.key === 'project' ? { ...tab, label } : tab
        )
      };
      tabStateRef.current = newState;
      return newState;
    }, { revalidate: false });
  }, [projectId, mutateTabState]);

  return {
    openTabs: tabState?.openTabs || [],
    activeTabKey: tabState?.activeTabKey || 'project',
    openTab,
    closeTab,
    closeTabByKey,
    selectTab,
    setProjectTabLabel,
  };
};