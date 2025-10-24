import { useCallback, useRef } from 'react';
import useSWR from 'swr';
import { UUID } from 'crypto';

export type TabType = 'project' | 'data_source' | 'dataset' | 'analysis' | 'automation' | 'pipeline' | 'model_entity';

export interface Tab {
  id: UUID | null;  // null = project tab
  closable?: boolean;
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

export const useTabContext = (projectId: UUID) => {
  // Use a ref to store the current tab state to prevent SWR from resetting it
  const tabStateRef = useRef<TabState>(getDefaultTabState());
  
  const { data: tabState, mutate: mutateTabState } = useSWR(
    `tabs-${projectId}`,
    () => tabStateRef.current, // Return the current state instead of default
    {
      fallbackData: getDefaultTabState(),
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      revalidateOnMount: false, // Prevent revalidation on mount
      revalidateIfStale: false, // Prevent revalidation if stale
    }
  );

  const openTab = useCallback((id: UUID | null, closable: boolean = true) => {
    mutateTabState((current: TabState | undefined) => {
      if (!current) {
        const defaultState = getDefaultTabState();
        tabStateRef.current = defaultState;
        return defaultState;
      }
      
      // If tab is already open, just activate it
      if (current.openTabs.some(t => t.id === id)) {
        const newState = { ...current, activeTabId: id };
        tabStateRef.current = newState;
        return newState;
      }
      
      // Add new tab
      const newState = {
        ...current,
        openTabs: [...current.openTabs, { id, closable }],
        activeTabId: id
      };
      tabStateRef.current = newState;
      return newState;
    }, { revalidate: false });
  }, [mutateTabState]);

  const closeTab = useCallback((id: UUID | null) => {
    mutateTabState((current: TabState | undefined) => {
      if (!current) {
        const defaultState = getDefaultTabState();
        tabStateRef.current = defaultState;
        return defaultState;
      }
      
      const filtered = current.openTabs.filter(tab => tab.id !== id);
      let newActiveTabId = current.activeTabId;
      
      // If closing the active tab, switch to the last tab (defaults to project tab)
      if (current.activeTabId === id) {
        newActiveTabId = filtered.length > 0 ? filtered[filtered.length - 1].id : null;
      }
      
      const newState = {
        ...current,
        openTabs: filtered,
        activeTabId: newActiveTabId
      };
      tabStateRef.current = newState;
      return newState;
    }, { revalidate: false });
  }, [mutateTabState]);

  const selectTab = useCallback((id: UUID | null) => {
    mutateTabState((current: TabState | undefined) => {
      if (!current) {
        const defaultState = getDefaultTabState();
        tabStateRef.current = defaultState;
        return defaultState;
      }
      const newState = { ...current, activeTabId: id };
      tabStateRef.current = newState;
      return newState;
    }, { revalidate: false });
  }, [mutateTabState]);

  return {
    openTabs: tabState?.openTabs || [],
    activeTabId: tabState?.activeTabId ?? null,
    openTab,
    closeTab,
    selectTab,
  };
};