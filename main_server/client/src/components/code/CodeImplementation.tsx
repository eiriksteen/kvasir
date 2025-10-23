"use client";

import { UUID } from "crypto";
import { useCode } from "@/hooks/useCodeStream";
import CodeDisplay from "@/components/code/CodeDisplay";

interface CodeImplementationProps {
  scriptId: UUID;
}

export default function CodeImplementation({ scriptId }: CodeImplementationProps) {
  const { script, error, isLoading } = useCode(scriptId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-500 text-sm">Loading script...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-red-500 text-sm">Error loading script: {error.message}</p>
      </div>
    );
  }

  if (!script) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-500 text-sm">Script not found</p>
      </div>
    );
  }

  return (
    <CodeDisplay
      filename={script.filename}
      code={script.code}
      output={script.output || ""}
      error={script.error || ""}
    />
  );
}
