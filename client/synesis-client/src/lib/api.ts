import { TimeSeriesDataset } from "@/types/datasets";

const API_URL = process.env.API_URL;

/**
 * Fetches time series datasets from the API
 * @param accessToken - The user's access token
 * @returns An array of time series datasets
 */
export async function fetchTimeSeriesDatasets(accessToken: string): Promise<TimeSeriesDataset[]> {
  try {
    const response = await fetch(`${API_URL}/ontology/time-series-datasets`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    });


    if (!response.ok) {
      const errorText = await response.text();
      console.error('Failed to fetch datasets', errorText);
      throw new Error(`Failed to fetch datasets: ${response.status} ${errorText}`);
    }

    const data = await response.json();
    return data;
    
  } catch (error) {
    console.error('Error fetching datasets:', error);
    return [];
  }
}

// Add function to fetch integration jobs
export async function fetchIntegrationJobs(token: string) {
  const response = await fetch(`${API_URL}/data/integration-jobs`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch integration jobs');
  }

  return response.json();
} 