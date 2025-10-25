import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check } from 'lucide-react';
import { useState } from 'react';

export const MarkdownComponents = {
    p: ({ children, ...props }: any) => (
      <p className="text-xs" {...props}>
        {children}
      </p>
    ),
    ul: ({ children, ...props }: any) => (
      <ul className="text-xs list-disc list-inside space-y-1 my-2" {...props}>
        {children}
      </ul>
    ),
    ol: ({ children, ...props }: any) => (
      <ol className="text-xs list-decimal list-inside space-y-1 my-2" {...props}>
        {children}
      </ol>
    ),
    li: ({ children, ...props }: any) => (
      <li className="text-xs" {...props}>
        {children}
      </li>
    ),
    table: ({ children, ...props }: any) => (
      <div className="overflow-x-auto w-[90%] mx-auto my-4">
        <table className="w-full border-collapse bg-[#1a1625] rounded-lg overflow-hidden border border-purple-700/30 shadow-lg" {...props}>
          {children}
        </table>
      </div>
    ),
    thead: ({ children, ...props }: any) => (
      <thead className="text-xs bg-purple-900/40 border-b border-purple-700/50" {...props}>
        {children}
      </thead>
    ),
    tbody: ({ children, ...props }: any) => (
      <tbody className="text-xs divide-y divide-purple-700/30" {...props}>
        {children}
      </tbody>
    ),
    tr: ({ children, ...props }: any) => (
      <tr className="hover:bg-purple-800/20 transition-colors duration-200" {...props}>
        {children}
      </tr>
    ),
    th: ({ children, ...props }: any) => (
      <th className="px-4 py-3 text-left text-xs font-semibold text-purple-200 border-r border-purple-700/30 last:border-r-0" {...props}>
        {children}
      </th>
    ),
    td: ({ children, ...props }: any) => (
      <td className="px-4 py-3 text-xs text-gray-300 border-r border-purple-700/30 last:border-r-0" {...props}>
        {children}
      </td>
    ),
    code: ({ node, inline, className, children, ...props }: any) => {
      const match = /language-(\w+)/.exec(className || '');
      const language = match ? match[1] : '';
      const [copied, setCopied] = useState(false);

      if (node) {
        return (
          <code className="markdown-inline-code" {...props}>
            {children}
          </code>
        );
      }

      const handleCopy = async () => {
        try {
          await navigator.clipboard.writeText(String(children).replace(/\n$/, ''));
          setCopied(true);
          setTimeout(() => setCopied(false), 2000);
        } catch (err) {
          console.error('Failed to copy code:', err);
        }
      };
  
      return (
        <div className="markdown-code-block" data-language={language}>
          <div className="rounded-sm overflow-hidden relative w-full">
            {/* Copy button */}
            <button
              onClick={handleCopy}
              className="absolute top-2 right-2 p-2 rounded-md bg-gray-300 hover:bg-gray-200 text-gray-100 hover:text-white transition-all duration-200 z-10"
              title="Copy code"
            >
              {copied ? <Check size={16} /> : <Copy size={16} />}
            </button>
            
            <div className="overflow-auto max-h-96" style={{ scrollbarWidth: 'thin', scrollbarColor: '#4B5563 #1F2937' }}>
              <SyntaxHighlighter
                style={oneLight}
                language={language}
                PreTag="div"
                customStyle={{
                  margin: 0,
                  background: 'white',
                  fontSize: '0.5rem',
                  padding: '1rem',
                  minWidth: '100%',
                }}
                {...props}
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            </div>
          </div>
        </div>
      );
    },
    pre: ({ children, ...props }: any) => (
      <pre className="markdown-code" {...props}>
        {children}
      </pre>
    ),
  };