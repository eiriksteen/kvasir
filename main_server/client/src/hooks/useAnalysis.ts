import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from 'swr/mutation'
import useSWRSubscription, { SWRSubscriptionOptions } from "swr/subscription";
import { 
  AnalysisObject, 
  AnalysisObjectCreate, 
  AnalysisStatusMessage,
  AnalysisResult,
  NotebookSectionCreate,
  NotebookSectionUpdate,
  SectionReorderRequest,
  SectionMoveRequest,
  NotebookSection,
  GenerateReportRequest,
  MoveRequest,
  AnalysisObjectSmall
} from "@/types/analysis";
import { AggregationObjectWithRawData } from "@/types/data-objects";
import { useProject } from "./useProject";
import { useMemo } from "react";
// import { useAgentContext } from './useAgentContext';
import { useRuns } from './useRuns';
import { Run } from "@/types/runs";
import { UUID } from "crypto";
import { SSE } from 'sse.js';
import { snakeToCamelKeys, camelToSnakeKeys } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL;


// routes for analysis object

export async function deleteAnalysisObjectEndpoint(token: string, analysisObjectId: string): Promise<void> {
  const response = await fetch(`${API_URL}/analysis/analysis-object/${analysisObjectId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to delete analysis object', errorText);
    throw new Error(`Failed to delete analysis object: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export async function fetchAnalysisObjects(token: string, projectId: UUID): Promise<AnalysisObjectSmall[]> {
  const response = await fetch(`${API_URL}/project/project-analyses/${projectId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text()
    console.error('Failed to fetch analysis objects', errorText);
    throw new Error(`Failed to fetch analysis objects: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export async function postAnalysisObject(token: string, analysisObjectCreate: AnalysisObjectCreate): Promise<AnalysisObject> {
  const response = await fetch(`${API_URL}/analysis/analysis-object`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(analysisObjectCreate))
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to create analysis object', errorText);
    throw new Error(`Failed to create analysis object: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export async function generateAnalysisReport(token: string, analysisObjectId: string, generateReportRequest: GenerateReportRequest): Promise<void> {
  const response = await fetch(`${API_URL}/analysis/analysis-object/${analysisObjectId}/generate-report`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(generateReportRequest))
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to generate analysis report', errorText);
    throw new Error(`Failed to generate analysis report: ${response.status} ${errorText}`);
  }

  const filename = generateReportRequest.filename + '.pdf';

  // Create a blob and download it
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

export function createAnalysisEventSource(token: string, jobId: string): SSE {
  return new SSE(`${API_URL}/analysis/analysis-agent-sse/${jobId}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    }
  );
}


export async function fetchAnalysisObject(token: string, analysisObjectId: string): Promise<AnalysisObject> {
  const response = await fetch(`${API_URL}/analysis/analysis-object/${analysisObjectId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch analysis object', errorText);
    throw new Error(`Failed to fetch analysis object: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export async function createNotebookSection(token: string, analysisObjectId: string, notebookSectionCreate: NotebookSectionCreate): Promise<NotebookSection> {
  const response = await fetch(`${API_URL}/analysis/analysis-object/${analysisObjectId}/create-section`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(notebookSectionCreate))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to create analysis section: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export async function updateNotebookSection(token: string, analysisObjectId: string, sectionId: string, sectionUpdate: NotebookSectionUpdate): Promise<NotebookSection> {
  const response = await fetch(`${API_URL}/analysis/analysis-object/${analysisObjectId}/section/${sectionId}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(sectionUpdate))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to update analysis section: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export async function updateAnalysisResult(token: string, analysisResultId: string, analysisResult: AnalysisResult): Promise<AnalysisResult> {
  const response = await fetch(`${API_URL}/analysis/analysis-result/${analysisResultId}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(analysisResult))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to update analysis result: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export async function deleteNotebookSectionEndpoint(token: string, analysisObjectId: string, sectionId: string): Promise<string> {
  const response = await fetch(`${API_URL}/analysis/analysis-object/${analysisObjectId}/section/${sectionId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to delete notebook section: ${response.status} ${errorText}`);
  }
  const data = await response.json();
  return snakeToCamelKeys(data);
}

export async function changeAnalysisResultSectionEndpoint(token: string, analysisResultId: string, newSectionId: string, oldSectionId: string): Promise<void> {
  const response = await fetch(`${API_URL}/analysis/analysis-result/${analysisResultId}/new-section/${newSectionId}/old-section/${oldSectionId}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to change analysis result section', errorText);
    throw new Error(`Failed to change analysis result section: ${response.status} ${errorText}`);
  }

  // returns nothing
  const data = await response.json();
  return snakeToCamelKeys(data);
}

export async function reorderNotebookSections(token: string, analysisObjectId: string, sectionReorderRequest: SectionReorderRequest): Promise<void> {
  const response = await fetch(`${API_URL}/analysis/analysis-object/${analysisObjectId}/reorder-sections`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(sectionReorderRequest))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to reorder notebook sections: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}


export async function moveNotebookSections(token: string, analysisObjectId: string, sectionMoveRequest: SectionMoveRequest): Promise<void> {
  const response = await fetch(`${API_URL}/analysis/analysis-object/${analysisObjectId}/move-sections`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(sectionMoveRequest))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to move notebook sections: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export async function getAnalysisResultDataEndpoint(token: string, analysisObjectId: string, analysisResultId: string): Promise<AggregationObjectWithRawData> {
  const response = await fetch(`${API_URL}/analysis/analysis-object/${analysisObjectId}/analysis-result/${analysisResultId}/get-data`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to get analysis result data: ${response.status} ${errorText}`);
  }

  // const arraybuffer = await response.arrayBuffer();
  let aggregationObjectWithRawData = await response.json();
  aggregationObjectWithRawData = snakeToCamelKeys(aggregationObjectWithRawData);
  for (const column of aggregationObjectWithRawData.data.outputData.data) {
    if (column.valueType === 'datetime') {
      column.values = column.values.map((timestamp: bigint) => new Date(Number(timestamp) / 1000000));
    }
  }
  
  return aggregationObjectWithRawData;
}

export async function moveElementEndpoint(token: string, analysisObjectId: string, moveRequest: MoveRequest): Promise<void> {
  const response = await fetch(`${API_URL}/analysis/analysis-object/${analysisObjectId}/move-element`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(moveRequest))
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to move element: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}


export async function deleteAnalysisResultEndpoint(token: string, analysisObjectId: string, analysisResultId: string): Promise<void> {
  const response = await fetch(`${API_URL}/analysis/analysis-object/${analysisObjectId}/analysis-result/${analysisResultId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to delete analysis result: ${response.status} ${errorText}`);
  }
}

export async function getAnalysisResultPlotsEndpoint(token: string, analysisObjectId: string, analysisResultId: string, plotUrl: string): Promise<string> {
  const response = await fetch(`${API_URL}/analysis/analysis-object/${analysisObjectId}/analysis-result/${analysisResultId}/${plotUrl}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    const errorText = await response.text();
    
    throw new Error(`Failed to get analysis result plots: ${response.status} ${errorText}`);
  }
  const url = URL.createObjectURL(await response.blob());
  return url;
} 


// hooks for analysis object


export const useAnalyses = (projectId: UUID) => {
    const { data: session } = useSession();

    // const { datasetsInContext, analysesInContext } = useAgentContext(projectId);

    const { addEntity } = useProject(projectId);
    
    const { data: analysisObjects, mutate: mutateAnalysisObjects } = useSWR(session && projectId ? ["analysisObjects", projectId] : null, () => fetchAnalysisObjects(session ? session.APIToken.accessToken : "", projectId), {fallbackData: [] as AnalysisObjectSmall[]});

    const { trigger: createAnalysisObject } = useSWRMutation(
      session && projectId ? ["analysisObjects", projectId] : null,
      async (_, { arg }: { arg: AnalysisObjectCreate }) => {
        const analysisObject = await postAnalysisObject(session ? session.APIToken.accessToken : "", arg);
        return analysisObject;
      },
      {
        populateCache: (analysisObject) => {
          if (analysisObjects) {
            return [...analysisObjects, analysisObject];
          }
          return [analysisObject];
        },
        revalidate: false
      }
    );

    const createAnalysis = async (analysisObjectCreate: AnalysisObjectCreate) => {
      const analysisObject = await createAnalysisObject(analysisObjectCreate);

      await addEntity("analysis", analysisObject.id);

    }


    return {
      analysisObjects: analysisObjects || [],
      mutateAnalysisObjects,
      createAnalysis
    };
  }

export const useAnalysis = (projectId: UUID, analysisObjectId: UUID) => {
  const { data: session } = useSession();
  const {data: currentAnalysisObject, mutate: mutateCurrentAnalysisObject} = useSWR(["analysisObject", analysisObjectId], () => fetchAnalysisObject(session?.APIToken.accessToken || "", analysisObjectId));

  const { analysisObjects, mutateAnalysisObjects } = useAnalyses(projectId);

  const { data: analysisResultData, mutate: mutateAnalysisResultData } = useSWR(["analysisResultData"], null, {fallbackData: {} as Record<UUID, AggregationObjectWithRawData>});

  const { trigger: deleteAnalysisObject } = useSWRMutation(
    "analysisObject",
    async (_, { arg }: { arg: { analysisObjectId: UUID } }) => {
      await deleteAnalysisObjectEndpoint(session ? session.APIToken.accessToken : "", arg.analysisObjectId);
    },
    {
      populateCache: () => {
        if (analysisObjects) {
          mutateAnalysisObjects(analysisObjects.filter(analysisObject => analysisObject.id !== analysisObjectId));
        }
      }
    }
  );

  const { trigger: generateReport } = useSWRMutation(
    "analysisObject",
    async (_, { arg }: { arg: { analysisObjectId: UUID, generateReportRequest: GenerateReportRequest } }) => {
      const analysisObject = await generateAnalysisReport(session ? session.APIToken.accessToken : "", arg.analysisObjectId, arg.generateReportRequest);
      return analysisObject;
    }
  );

  const { data: analysisStatusMessages, mutate: mutateAnalysisStatusMessages } = useSWR(["analysisStatusMessages", analysisObjectId], null, {fallbackData: [] as AnalysisStatusMessage[]});

  const { runs } = useRuns();

  const runningJobs = useMemo(() => {
    if (!runs) return [];
    return runs.filter((run: Run) => run.status === "running").sort((a: Run, b: Run) => new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime());
  }, [runs]);

  // Subscribe to streaming updates for the first running job
  // Note: For multiple running runs, we would need a more complex implementation
  const firstRunningJob = runningJobs[0];
  useSWRSubscription<AnalysisStatusMessage[]>(
    session && firstRunningJob ? ["analysis-agent-stream", firstRunningJob.id, analysisObjectId] : null,
    (_: string, { next }: SWRSubscriptionOptions<AnalysisStatusMessage[]>) => {
      if (!session?.APIToken?.accessToken) {
        return;
      }
      mutateCurrentAnalysisObject();
      const eventSource = createAnalysisEventSource(session.APIToken.accessToken, firstRunningJob.id);
      eventSource.onmessage = (event) => {
        const newMessage = JSON.parse(event.data) as AnalysisStatusMessage;

        // Append the new message to analysisStatusMessages, deduplicating by id
        mutateAnalysisStatusMessages((current: AnalysisStatusMessage[] = []) => {
          if (current.some(m => m.id === newMessage.id)) return current;
          const updated = [...current, newMessage];

          return updated;
        }, true); // true = revalidate to trigger re-renders
        
        // Trigger the subscription to update
        next(null, undefined);
      };
      return () => {
        eventSource.close();
        mutateCurrentAnalysisObject();
        mutateAnalysisStatusMessages([]);
      };
    },
    { fallbackData: [] }
  );
  

  const { trigger: createSection } = useSWRMutation(
    "analysisObject",
    async (_, { arg }: { arg: { sectionName: string, sectionDescription: string | null, parentSectionId: UUID | null } }) => {
      if (!currentAnalysisObject?.notebook?.id) {
        throw new Error("No notebook found");
      }

      const notebookSectionCreate: NotebookSectionCreate = {
        analysisObjectId: analysisObjectId,
        sectionName: arg.sectionName,
        sectionDescription: arg.sectionDescription,
        parentSectionId: arg.parentSectionId
      };

      const section = await createNotebookSection(
        session ? session.APIToken.accessToken : "", 
        analysisObjectId,
        notebookSectionCreate
      );
      return section;
    },
    {
      populateCache: () => {
        mutateCurrentAnalysisObject();
      }
    }
  );

  const { trigger: updateSection } = useSWRMutation(
    "analysisObject",
    async (_, { arg }: { arg: { sectionId: UUID, sectionUpdate: NotebookSectionUpdate } }) => {
      const section = await updateNotebookSection(
        session ? session.APIToken.accessToken : "", 
        analysisObjectId,
        arg.sectionId,
        arg.sectionUpdate
      );
      return section;
    },
    {
      populateCache: () => {
        mutateCurrentAnalysisObject();
      }
    }
  );

  const { trigger: updateAnalysisResultMutation } = useSWRMutation(
    "analysisObject",
    async (_, { arg }: { arg: { analysisResultId: UUID, analysisResult: AnalysisResult } }): Promise<AnalysisResult> => {
      const analysisResult: AnalysisResult = await updateAnalysisResult(
        session ? session.APIToken.accessToken : "", 
        arg.analysisResultId,
        arg.analysisResult
      );
      return analysisResult;
    },
    {
      populateCache: () => {
        mutateCurrentAnalysisObject();
      }
    }
  );

  const { trigger: deleteSection } = useSWRMutation(
    "analysisObject",
    async (_, { arg }: { arg: { sectionId: UUID } }) => {
      await deleteNotebookSectionEndpoint(session ? session.APIToken.accessToken : "", analysisObjectId, arg.sectionId);
      return arg.sectionId;
    },
    {
      populateCache: () => {
        mutateCurrentAnalysisObject();
      }
    }
  );

  const { trigger: changeAnalysisResultSection } = useSWRMutation(
    "analysisObject",
    async (_, { arg }: { arg: { analysisResultId: UUID, newSectionId: UUID, oldSectionId: UUID } }) => {
      await changeAnalysisResultSectionEndpoint(session ? session.APIToken.accessToken : "", arg.analysisResultId, arg.newSectionId, arg.oldSectionId);
    },
    {
      populateCache: () => {
        mutateCurrentAnalysisObject();
      }
    }
  );

  const { trigger: reorderSections } = useSWRMutation(
    "analysisObject",
    async (_, { arg }: { arg: { analysisObjectId: UUID, sectionReorderRequest: SectionReorderRequest } }) => {
      await reorderNotebookSections(session ? session.APIToken.accessToken : "", arg.analysisObjectId, arg.sectionReorderRequest);
    },
    {
      populateCache: () => {
        mutateCurrentAnalysisObject();
      }
    }
  );

  const { trigger: moveSections } = useSWRMutation(
    "analysisObject",
    async (_, { arg }: { arg: { analysisObjectId: UUID, sectionMoveRequest: SectionMoveRequest } }) => {
      await moveNotebookSections(session ? session.APIToken.accessToken : "", arg.analysisObjectId, arg.sectionMoveRequest);
    },
    {
      populateCache: () => {
        mutateCurrentAnalysisObject();
      }
    }
  );

  const { trigger: getAnalysisResultData } = useSWRMutation(
    "analysisObject",
    async (_, { arg }: { arg: { analysisObjectId: UUID, analysisResultId: UUID } }) => {
      const data = await getAnalysisResultDataEndpoint(session ? session.APIToken.accessToken : "", arg.analysisObjectId, arg.analysisResultId);
      return {analysisResultId: arg.analysisResultId, data: data};
    },
    {
      populateCache: (data) => {
        mutateAnalysisResultData((current: Record<UUID, AggregationObjectWithRawData> = {}) => ({...current, [data.analysisResultId]: data.data}));
      }
    }
  );
  
  const { trigger: moveElement } = useSWRMutation(
    "analysisObject",
    async (_, { arg }: { arg: { analysisObjectId: UUID, moveRequest: MoveRequest } }) => {
      await moveElementEndpoint(session ? session.APIToken.accessToken : "", arg.analysisObjectId, arg.moveRequest);
    },
    {
      populateCache: () => {
        mutateCurrentAnalysisObject();
      }
    }
  );
  const { trigger: deleteAnalysisResult } = useSWRMutation(
    "analysisObject",
    async (_, { arg }: { arg: { analysisObjectId: UUID, analysisResultId: UUID } }) => {
      await deleteAnalysisResultEndpoint(session ? session.APIToken.accessToken : "", arg.analysisObjectId, arg.analysisResultId);
    },
    {
      populateCache: () => {
        mutateCurrentAnalysisObject();
      }
    }
  );

  const { data: analysisResultPlots, mutate: mutateAnalysisResultPlots } = useSWR(["analysisResultPlots"], null, {fallbackData: {} as Record<UUID, string[]>});

  const { trigger: getAnalysisResultPlots } = useSWRMutation(
    "analysisObject",
    async (_, { arg }: { arg: { analysisObjectId: UUID, analysisResultId: UUID, plotUrls: string[] } }) => {
      // Fetch all plots and convert them to blob URLs
      const plotBlobUrls = await Promise.all(
        arg.plotUrls.map(plotUrl => 
          getAnalysisResultPlotsEndpoint(
            session ? session.APIToken.accessToken : "", 
            arg.analysisObjectId, 
            arg.analysisResultId, 
            plotUrl
          )
        )
      );
      return {analysisResultId: arg.analysisResultId, plots: plotBlobUrls};
    },
    {
      populateCache: (data) => {
        mutateAnalysisResultPlots((current: Record<UUID, string[]> = {}) => ({...current, [data.analysisResultId]: data.plots}));
      }
    }
  );


  return {
    currentAnalysisObject,
    deleteAnalysisObject,
    generateReport,
    analysisStatusMessages,
    createSection,
    updateSection,
    updateAnalysisResult: updateAnalysisResultMutation,
    deleteSection,
    changeAnalysisResultSection,
    reorderSections,
    moveSections,
    getAnalysisResultData,
    analysisResultData,
    moveElement,
    deleteAnalysisResult,
    getAnalysisResultPlots,
    analysisResultPlots
  }
}