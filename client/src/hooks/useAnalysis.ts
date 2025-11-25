import { useSession } from "next-auth/react";
import { useMemo } from "react";
import useSWR from "swr";
import useSWRSubscription, { SWRSubscriptionOptions } from "swr/subscription";
import { UUID } from "crypto";
import { SSE } from 'sse.js';
import { snakeToCamelKeys } from "@/lib/utils";
import { 
  Analysis, 
  AnalysisCell,
  Section,
} from "@/types/ontology/analysis";
import { useAnalysisRuns } from "@/hooks/useRuns";


const API_URL = process.env.NEXT_PUBLIC_API_URL;

// =============================================================================
// API Functions
// =============================================================================

async function fetchAnalysis(token: string, analysisId: UUID): Promise<Analysis> {
  const response = await fetch(`${API_URL}/analysis/analysis/${analysisId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch analysis', errorText);
    throw new Error(`Failed to fetch analysis: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}



function createAnalysisEventSource(token: string, runId: UUID): SSE {
  return new SSE(`${API_URL}/analysis/analysis-agent-sse/${runId}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    }
  );
}

// =============================================================================
// Hooks
// =============================================================================



export const useAnalysis = (projectId: UUID, analysisId: UUID) => {
  const { data: session } = useSession();

  // Fetch the analysis
  const { data: analysis, mutate: mutateAnalysis, error, isLoading } = useSWR(
    session && analysisId ? ["analysis", analysisId] : null,
    () => fetchAnalysis(session!.APIToken.accessToken, analysisId!)
  );  

  const { analysisRuns } = useAnalysisRuns(projectId, analysisId);

  const runningID = useMemo(() => {
    // For now assume only one run going for an analysis at a time
    return analysisRuns.filter(run => run.status === "running").map(run => run.id)[0] ?? null;
  }, [analysisRuns]) as UUID | null;

  // SSE streaming for real-time updates
  const { data: streamedUpdates } = useSWRSubscription<(Section | AnalysisCell)[]>(
    session && runningID ? ["analysis-stream", analysisId, runningID] : null,
    (_: string, { next }: SWRSubscriptionOptions<(Section | AnalysisCell)[]>) => {
      if (!session?.APIToken?.accessToken || !runningID) {
        return;
      }

      const eventSource = createAnalysisEventSource(session.APIToken.accessToken, runningID);
      const updates: (Section | AnalysisCell)[] = [];

      eventSource.onmessage = (event) => {
        const rawMessage = JSON.parse(event.data);
        const update = snakeToCamelKeys(rawMessage) as Section | AnalysisCell;
        
        updates.push(update);
        
        // Update the in-memory analysis object directly
        mutateAnalysis((currentAnalysis) => {
          if (!currentAnalysis) return currentAnalysis;
          
          // Check if this is a Section or AnalysisCell
          if ('cells' in update) {
            const section = update as Section;
            const sectionExists = currentAnalysis.sections.some(s => s.id === section.id);
            
            if (sectionExists) {
              return {
                ...currentAnalysis,
                sections: currentAnalysis.sections.map(s => 
                  s.id === section.id ? section : s
                )
              };
            } else {
              return {
                ...currentAnalysis,
                sections: [...currentAnalysis.sections, section]
              };
            }
          } else {
            const cell = update as AnalysisCell;
            return {
              ...currentAnalysis,
              sections: currentAnalysis.sections.map(section => {
                if (section.id === cell.sectionId) {
                  const cellExists = section.cells.some(c => c.id === cell.id);
                  if (cellExists) {
                    return {
                      ...section,
                      cells: section.cells.map(c => c.id === cell.id ? cell : c)
                    };
                  } else {
                    return {
                      ...section,
                      cells: [...section.cells, cell]
                    };
                  }
                }
                return section;
              })
            };
          }
        }, { revalidate: false });
        
        next(null, updates);
      };

      eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        eventSource.close();
      };

      return () => {
        eventSource.close();
      };
    },
    { fallbackData: [] }
  );

  return {
    analysis,
    mutateAnalysis,
    error,
    isLoading,
    // Streaming updates
    streamedUpdates,
  };
};
