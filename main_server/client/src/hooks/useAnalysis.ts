import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from 'swr/mutation'
import useSWRSubscription, { SWRSubscriptionOptions } from "swr/subscription";
import { UUID } from "crypto";
import { SSE } from 'sse.js';
import { snakeToCamelKeys, camelToSnakeKeys } from "@/lib/utils";
import { 
  Analysis, 
  AnalysisCell,
  Section,
  SectionCreate,
  CodeCellCreate,
  MarkdownCellCreate,
  CodeOutputCreate,
} from "@/types/ontology/analysis";
import { 
  ImageCreate,
  EchartCreate,
  TableCreate,
} from "@/types/ontology/visualization";

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

async function fetchAnalysesByIds(token: string, analysisIds: UUID[]): Promise<Analysis[]> {
  const response = await fetch(`${API_URL}/analysis/analyses-by-ids`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(analysisIds)
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch analyses by ids', errorText);
    throw new Error(`Failed to fetch analyses by ids: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function createSection(token: string, analysisId: UUID, sectionCreate: SectionCreate): Promise<Analysis> {
  const response = await fetch(`${API_URL}/analysis/analysis/${analysisId}/section`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(sectionCreate))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to create section: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function createMarkdownCell(token: string, analysisId: UUID, markdownCellCreate: MarkdownCellCreate): Promise<AnalysisCell> {
  const response = await fetch(`${API_URL}/analysis/analysis/${analysisId}/markdown-cell`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(markdownCellCreate))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to create markdown cell: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function createCodeCell(token: string, analysisId: UUID, codeCellCreate: CodeCellCreate): Promise<AnalysisCell> {
  const response = await fetch(`${API_URL}/analysis/analysis/${analysisId}/code-cell`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(codeCellCreate))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to create code cell: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function createCodeOutput(token: string, analysisId: UUID, codeOutputCreate: CodeOutputCreate): Promise<Analysis> {
  const response = await fetch(`${API_URL}/analysis/analysis/${analysisId}/code-output`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(codeOutputCreate))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to create code output: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function createCodeOutputImage(token: string, analysisId: UUID, codeCellId: UUID, imageCreate: ImageCreate): Promise<Analysis> {
  const response = await fetch(`${API_URL}/analysis/analysis/${analysisId}/code-cell/${codeCellId}/image`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(imageCreate))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to create code output image: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function createCodeOutputEchart(token: string, analysisId: UUID, codeCellId: UUID, echartCreate: EchartCreate): Promise<Analysis> {
  const response = await fetch(`${API_URL}/analysis/analysis/${analysisId}/code-cell/${codeCellId}/echart`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(echartCreate))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to create code output echart: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

async function createCodeOutputTable(token: string, analysisId: UUID, codeCellId: UUID, tableCreate: TableCreate): Promise<Analysis> {
  const response = await fetch(`${API_URL}/analysis/analysis/${analysisId}/code-cell/${codeCellId}/table`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(tableCreate))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to create code output table: ${response.status} ${errorText}`);
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

/**
 * Hook to fetch analyses by IDs.
 * For fetching all analyses in a project, use useOntology instead.
 */
export const useAnalysesByIds = (analysisIds?: UUID[]) => {
  const { data: session } = useSession();

  const { data: analyses, mutate: mutateAnalyses, error, isLoading } = useSWR(
    session && analysisIds && analysisIds.length > 0 ? ["analyses-by-ids", analysisIds] : null,
    () => fetchAnalysesByIds(session!.APIToken.accessToken, analysisIds || [])
  );

  return {
    analyses,
    mutateAnalyses,
    error,
    isLoading,
  };
};

/**
 * Hook to fetch and interact with a single analysis.
 * 
 * This hook provides:
 * - Analysis data with sections and cells
 * - Mutations for creating sections, cells, and outputs
 * - SSE streaming for real-time updates during analysis runs
 * 
 * Note: For creating/deleting analyses, use useOntology hook.
 */
export const useAnalysis = (analysisId?: UUID) => {
  const { data: session } = useSession();

  // Fetch the analysis
  const { data: analysis, mutate: mutateAnalysis, error, isLoading } = useSWR(
    session && analysisId ? ["analysis", analysisId] : null,
    () => fetchAnalysis(session!.APIToken.accessToken, analysisId!)
  );

  // Section mutations
  const { trigger: triggerCreateSection } = useSWRMutation(
    ["analysis", analysisId],
    async (_, { arg }: { arg: SectionCreate }) => {
      const updatedAnalysis = await createSection(
        session!.APIToken.accessToken,
        analysisId!,
        arg
      );
      await mutateAnalysis(updatedAnalysis);
      return updatedAnalysis;
    }
  );

  // Cell mutations
  const { trigger: triggerCreateMarkdownCell } = useSWRMutation(
    ["analysis", analysisId],
    async (_, { arg }: { arg: MarkdownCellCreate }) => {
      const cell = await createMarkdownCell(
        session!.APIToken.accessToken,
        analysisId!,
        arg
      );
      await mutateAnalysis();
      return cell;
    }
  );

  const { trigger: triggerCreateCodeCell } = useSWRMutation(
    ["analysis", analysisId],
    async (_, { arg }: { arg: CodeCellCreate }) => {
      const cell = await createCodeCell(
        session!.APIToken.accessToken,
        analysisId!,
        arg
      );
      await mutateAnalysis();
      return cell;
    }
  );

  // Code output mutations
  const { trigger: triggerCreateCodeOutput } = useSWRMutation(
    ["analysis", analysisId],
    async (_, { arg }: { arg: CodeOutputCreate }) => {
      const updatedAnalysis = await createCodeOutput(
        session!.APIToken.accessToken,
        analysisId!,
        arg
      );
      await mutateAnalysis(updatedAnalysis);
      return updatedAnalysis;
    }
  );

  const { trigger: triggerCreateCodeOutputImage } = useSWRMutation(
    ["analysis", analysisId],
    async (_, { arg }: { arg: { codeCellId: UUID; imageCreate: ImageCreate } }) => {
      const updatedAnalysis = await createCodeOutputImage(
        session!.APIToken.accessToken,
        analysisId!,
        arg.codeCellId,
        arg.imageCreate
      );
      await mutateAnalysis(updatedAnalysis);
      return updatedAnalysis;
    }
  );

  const { trigger: triggerCreateCodeOutputEchart } = useSWRMutation(
    ["analysis", analysisId],
    async (_, { arg }: { arg: { codeCellId: UUID; echartCreate: EchartCreate } }) => {
      const updatedAnalysis = await createCodeOutputEchart(
        session!.APIToken.accessToken,
        analysisId!,
        arg.codeCellId,
        arg.echartCreate
      );
      await mutateAnalysis(updatedAnalysis);
      return updatedAnalysis;
    }
  );

  const { trigger: triggerCreateCodeOutputTable } = useSWRMutation(
    ["analysis", analysisId],
    async (_, { arg }: { arg: { codeCellId: UUID; tableCreate: TableCreate } }) => {
      const updatedAnalysis = await createCodeOutputTable(
        session!.APIToken.accessToken,
        analysisId!,
        arg.codeCellId,
        arg.tableCreate
      );
      await mutateAnalysis(updatedAnalysis);
      return updatedAnalysis;
    }
  );

  // SSE streaming for real-time updates
  const { data: streamedUpdates } = useSWRSubscription<(Section | AnalysisCell)[]>(
    session && analysisId ? ["analysis-stream", analysisId] : null,
    (_: string, { next }: SWRSubscriptionOptions<(Section | AnalysisCell)[]>) => {
      if (!session?.APIToken?.accessToken || !analysisId) {
        return;
      }

      const eventSource = createAnalysisEventSource(session.APIToken.accessToken, analysisId);
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

    // Section operations
    createSection: triggerCreateSection,

    // Cell operations
    createMarkdownCell: triggerCreateMarkdownCell,
    createCodeCell: triggerCreateCodeCell,

    // Code output operations
    createCodeOutput: triggerCreateCodeOutput,
    createCodeOutputImage: triggerCreateCodeOutputImage,
    createCodeOutputEchart: triggerCreateCodeOutputEchart,
    createCodeOutputTable: triggerCreateCodeOutputTable,

    // Streaming updates
    streamedUpdates,
  };
};
