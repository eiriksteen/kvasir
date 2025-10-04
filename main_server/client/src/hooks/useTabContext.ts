import { useCallback } from 'react';
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

// Fetcher function for SWR
const fetcher = (projectId: UUID): TabState => {
  // In a real app, you might want to persist this to localStorage or a backend
  // For now, we'll just return the default state
  return getDefaultTabState(projectId);
};

export const useTabContext = (projectId: UUID) => {
  const { data: tabState, mutate: mutateTabState } = useSWR(
    `tabs-${projectId}`,
    () => fetcher(projectId),
    {
      fallbackData: getDefaultTabState(projectId),
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
    }
  );

  const openTab = useCallback((tab: Omit<Tab, 'key'>) => {
    const key = `${tab.type}-${tab.id}`;
    mutateTabState((current: TabState | undefined) => {
      if (!current) return getDefaultTabState(projectId);
      
      if (current.openTabs.some(t => t.key === key)) {
        return { ...current, activeTabKey: key };
      }
      
      return {
        ...current,
        openTabs: [...current.openTabs, { ...tab, key }],
        activeTabKey: key
      };
    }, { revalidate: false });
  }, [projectId, mutateTabState]);

  const closeTab = useCallback((entityId: string, entityType: TabType) => {
    const key = `${entityType}-${entityId}`;
    closeTabByKey(key);
  }, []);

  const closeTabByKey = useCallback((key: string) => {
    mutateTabState((current: TabState | undefined) => {
      if (!current) return getDefaultTabState(projectId);
      
      const filtered = current.openTabs.filter(tab => tab.key !== key);
      let newActiveTabKey = current.activeTabKey;
      
      // If closing the active tab, switch to the last tab (never closes project tab)
      if (current.activeTabKey === key) {
        newActiveTabKey = filtered.length > 0 ? filtered[filtered.length - 1].key : 'project';
      }
      
      return {
        ...current,
        openTabs: filtered,
        activeTabKey: newActiveTabKey
      };
    }, { revalidate: false });
  }, [projectId, mutateTabState]);

  const selectTab = useCallback((key: string) => {
    mutateTabState((current: TabState | undefined) => {
      if (!current) return getDefaultTabState(projectId);
      return { ...current, activeTabKey: key };
    }, { revalidate: false });
  }, [mutateTabState]);

  const setProjectTabLabel = useCallback((label: string) => {
    mutateTabState((current: TabState | undefined) => {
      if (!current) return getDefaultTabState(projectId);
      
      return {
        ...current,
        openTabs: current.openTabs.map(tab =>
          tab.key === 'project' ? { ...tab, label } : tab
        )
      };
    }, { revalidate: false });
  }, [mutateTabState]);

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