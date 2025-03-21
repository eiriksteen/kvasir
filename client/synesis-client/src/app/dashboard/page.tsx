import { getServerSession } from "next-auth/next"
import { authOptions } from "@/app/api/auth/[...nextauth]/route";
import { redirect } from "next/navigation";
import DashboardContainer from "@/app/dashboard/container";
import { fetchTimeSeriesDatasets, fetchIntegrationJobs } from "@/lib/api";
import { JobMetadata } from "@/types/jobs";

export default async function Home() {
  const session = await getServerSession(authOptions);

  if (!session) {
    redirect('/login');
  }

  // Fetch real datasets from API
  const datasets = await fetchTimeSeriesDatasets(session.APIToken.accessToken);
  
  // Fetch integration jobs
  let integrationJobs: JobMetadata[] = [];
  try {
    integrationJobs = await fetchIntegrationJobs(session.APIToken.accessToken);
  } catch (error) {
    console.error("Failed to fetch integration jobs:", error);
  }


  return (
    <>
      <DashboardContainer datasets={datasets} integrationJobs={integrationJobs} analysisJobs={[]} automationJobs={[]} />
    </>
  );
}
