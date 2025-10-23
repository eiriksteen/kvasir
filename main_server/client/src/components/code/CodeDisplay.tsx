interface CodeViewProps {
  filename: string;
  code: string;
  output: string;
  error: string;
}

export default function CodeDisplay({ filename, code, output, error }: CodeViewProps) {
  return (
    <div className="h-full flex flex-col">
        <div className="flex flex-col h-full">
          <div className="bg-gray-100 border-b border-gray-300 px-4 py-2 sticky top-0 z-10">
            <p className="text-xs font-mono font-semibold text-gray-800">
              {filename}
            </p>
          </div>
          <div className="flex-1 overflow-auto">
            <pre className="text-black p-4 text-xs font-mono leading-relaxed">
              {code}
            </pre>
          </div>
          {output && (
            <div className="border-t border-gray-300 bg-blue-50 p-3">
              <p className="text-xs font-semibold text-gray-700 mb-1">Output:</p>
              <pre className="text-xs font-mono">{output}</pre>
            </div>
          )}
          {error && (
            <div className="border-t border-red-300 bg-red-50 p-3">
              <p className="text-xs font-semibold text-red-700 mb-1">Error:</p>
              <pre className="text-xs font-mono text-red-600">{error}</pre>
            </div>
          )}
        </div>
    </div>
  );
}

