"use client";

import { UUID } from "crypto";
import { useCodebaseTree } from "@/hooks/useCodebase";
import CodeView from "@/components/code/CodeDisplay";

interface CodeStreamProps {
  runId: UUID;
}

export default function CodeStream({ runId }: CodeStreamProps) {
  const { codeMessage } = useCodebaseTree(runId);

  return ( 
    <>
      {codeMessage ? (
        <CodeView filename={codeMessage.filename ?? ""} code={codeMessage.code ?? ""} output={codeMessage.output ?? ""} error={codeMessage.error ?? ""} />
      ) : (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-500 text-sm">No code messages yet...</p>
        </div>
      )}
    </>
  )
}

