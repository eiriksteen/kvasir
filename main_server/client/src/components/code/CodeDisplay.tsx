interface CodeViewProps {
  filename: string;
  code: string;
  output: string;
  error: string;
}

export default function CodeDisplay({ code, output, error }: CodeViewProps) {
  return (
    <div className="h-full w-full flex flex-col">
        <div className="flex flex-col h-full w-full">
          {/* <div className="bg-gray-100 border-b border-gray-300 px-4 py-2 sticky top-0 z-10">
            <p className="text-xs font-mono font-semibold text-gray-800">
              {filename}
            </p>
          </div> */}
          <div className="flex-1 overflow-auto w-full">
            <pre className="text-black p-4 text-xs font-mono leading-relaxed whitespace-pre-wrap break-words">
              {code}
            </pre>
          </div>
          {output && (
            <div className="border-t border-gray-300 bg-blue-50 p-3 w-full">
              <p className="text-xs font-semibold text-gray-700 mb-1">Output:</p>
              <pre className="text-xs font-mono whitespace-pre-wrap break-words">{output}</pre>
            </div>
          )}
          {error && (
            <div className="border-t border-red-300 bg-red-50 p-3 w-full">
              <p className="text-xs font-semibold text-red-700 mb-1">Error:</p>
              <pre className="text-xs font-mono text-red-600 whitespace-pre-wrap break-words">{error}</pre>
            </div>
          )}
        </div>
    </div>
  );
}

