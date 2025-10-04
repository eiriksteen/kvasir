import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from 'swr/mutation';
import { UUID } from "crypto";
import { PlotUpdate } from "@/types/plots";
import { snakeToCamelKeys, camelToSnakeKeys } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// routes for plots

export async function createPlotEndpoint(token: string, plotCreate: any): Promise<any> {
  const response = await fetch(`${API_URL}/plots/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(plotCreate))
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to create plot', errorText);
    throw new Error(`Failed to create plot: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export async function fetchPlotEndpoint(token: string, plotId: string): Promise<any> {
  const response = await fetch(`${API_URL}/plots/${plotId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch plot', errorText);
    throw new Error(`Failed to fetch plot: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export async function fetchPlotsByAnalysisResultEndpoint(token: string, analysisResultId: string): Promise<any[]> {
  const response = await fetch(`${API_URL}/plots/analysis-result/${analysisResultId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to fetch plots by analysis result', errorText);
    throw new Error(`Failed to fetch plots by analysis result: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export async function updatePlotEndpoint(token: string, plotId: string, plotUpdate: any): Promise<any> {
  const response = await fetch(`${API_URL}/plots/${plotId}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(camelToSnakeKeys(plotUpdate))
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to update plot', errorText);
    throw new Error(`Failed to update plot: ${response.status} ${errorText}`);
  }

  const data = await response.json();
  return snakeToCamelKeys(data);
}

export async function deletePlotEndpoint(token: string, plotId: string): Promise<void> {
  const response = await fetch(`${API_URL}/plots/${plotId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error('Failed to delete plot', errorText);
    throw new Error(`Failed to delete plot: ${response.status} ${errorText}`);
  }
}

















// Hook for managing plots for a specific analysis result
export const usePlots = (analysisResultId: UUID) => {
  const { data: session } = useSession();

  const { data: plots, mutate: mutatePlots } = useSWR(
    ["plots", analysisResultId], 
    () => fetchPlotsByAnalysisResultEndpoint(session?.APIToken.accessToken || "", analysisResultId)
  );

  const { trigger: createPlot } = useSWRMutation(
    "plots",
    async (_, { arg }: { arg: { plotCreate: any } }) => {
      const plot = await createPlotEndpoint(session ? session.APIToken.accessToken : "", arg.plotCreate);
      return plot;
    },
    {
      populateCache: (newPlot) => {
        mutatePlots((current: any[] = []) => [...current, newPlot]);
      }
    }
  );

  const { trigger: updatePlot } = useSWRMutation(
    "plots",
    async (_, { arg }: { arg: { plotId: string, plotUpdate: PlotUpdate } }) => {
      const plot = await updatePlotEndpoint(session ? session.APIToken.accessToken : "", arg.plotId, arg.plotUpdate);
      return plot;
    },
    {
      populateCache: (updatedPlot) => {
        mutatePlots((current: any[] = []) => 
          current.map(plot => plot.id === updatedPlot.id ? updatedPlot : plot)
        );
      }
    }
  );

  const { trigger: deletePlot } = useSWRMutation(
    "plots",
    async (_, { arg }: { arg: { plotId: string } }) => {
      await deletePlotEndpoint(session ? session.APIToken.accessToken : "", arg.plotId);
      return arg.plotId;
    },
    {
      populateCache: (deletedPlotId) => {
        mutatePlots((current: any[] = []) => 
          current.filter(plot => plot.id !== deletedPlotId)
        );
      }
    }
  );

  return {
    plots,
    mutatePlots,
    createPlot,
    updatePlot,
    deletePlot
  };
};