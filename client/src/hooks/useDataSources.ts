import { useSession } from "next-auth/react";
import useSWR from "swr";
import useSWRMutation from "swr/mutation";
import { fetchDataSources, createFileDataSource } from "@/lib/api";


export const useDataSources = () => {
  const { data: session } = useSession();
  const { data: dataSources, error, isLoading } = useSWR(session ? "data-sources" : null, () => fetchDataSources(session ? session.APIToken.accessToken : ""));

  const { trigger: triggerCreateFileDataSource } = useSWRMutation(
    session ? "data-sources" : null,
    async (_, { arg }: { arg: { files: File[] } }) => {
      const newDataSource = await createFileDataSource(session ? session.APIToken.accessToken : "", arg.files);
      return [...(dataSources || []), newDataSource];
    }
  );

  return { dataSources, error, isLoading, triggerCreateFileDataSource };
}