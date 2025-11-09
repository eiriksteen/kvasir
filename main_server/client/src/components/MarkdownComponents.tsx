import React, { useState, ReactNode } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check } from 'lucide-react';

interface BaseComponentProps extends React.HTMLAttributes<HTMLElement> {
  children?: ReactNode;
}

interface CodeComponentProps extends BaseComponentProps {
  inline?: boolean;
  className?: string;
}

const CodeBlock = ({ inline, className, children, ...props }: CodeComponentProps) => {
  const match = /language-(\w+)/.exec(className || '');
  const language = match ? match[1] : '';
  const [copied, setCopied] = useState(false);

  if (inline) {
    return (
      <code className="bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded text-xs font-mono" {...props}>
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
    <span className="block relative w-full my-4" data-language={language}>
      <span className="block rounded-lg overflow-hidden border border-gray-200 bg-white">
        {/* Copy button */}
        <button
          onClick={handleCopy}
          className="absolute top-2 right-2 p-2 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-600 hover:text-gray-800 transition-all duration-200 z-10"
          title="Copy code"
        >
          {copied ? <Check size={16} /> : <Copy size={16} />}
        </button>
        
        <SyntaxHighlighter
          style={oneLight}
          language={language}
          PreTag="span"
          customStyle={{
            margin: 0,
            background: 'white',
            fontSize: '0.75rem',
            padding: '1rem',
            minWidth: '100%',
            maxHeight: '24rem',
            overflow: 'auto',
            display: 'block',
          }}
          {...props}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      </span>
    </span>
  );
};

export const MarkdownComponents = {
    p: ({ children, ...props }: BaseComponentProps) => (
      <p className="text-sm leading-relaxed mb-3" {...props}>
        {children}
      </p>
    ),
    ul: ({ children, ...props }: BaseComponentProps) => (
      <ul className="text-sm list-disc list-inside space-y-1 my-3 ml-4" {...props}>
        {children}
      </ul>
    ),
    ol: ({ children, ...props }: BaseComponentProps) => (
      <ol className="text-sm list-decimal list-inside space-y-1 my-3 ml-4" {...props}>
        {children}
      </ol>
    ),
    li: ({ children, ...props }: BaseComponentProps) => (
      <li className="text-sm leading-relaxed" {...props}>
        {children}
      </li>
    ),
    table: ({ children, ...props }: BaseComponentProps) => (
      <div className="overflow-x-auto w-[90%] mx-auto my-4">
        <table className="w-full border-collapse bg-white rounded-lg overflow-hidden border border-gray-300 shadow-sm" {...props}>
          {children}
        </table>
      </div>
    ),
    thead: ({ children, ...props }: BaseComponentProps) => (
      <thead className="text-sm bg-gray-50 border-b border-gray-300" {...props}>
        {children}
      </thead>
    ),
    tbody: ({ children, ...props }: BaseComponentProps) => (
      <tbody className="text-sm divide-y divide-gray-200" {...props}>
        {children}
      </tbody>
    ),
    tr: ({ children, ...props }: BaseComponentProps) => (
      <tr className="hover:bg-gray-50 transition-colors duration-200" {...props}>
        {children}
      </tr>
    ),
    th: ({ children, ...props }: BaseComponentProps) => (
      <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 border-r border-gray-300 last:border-r-0" {...props}>
        {children}
      </th>
    ),
    td: ({ children, ...props }: BaseComponentProps) => (
      <td className="px-4 py-3 text-sm text-gray-700 border-r border-gray-300 last:border-r-0" {...props}>
        {children}
      </td>
    ),
    code: CodeBlock,
    pre: ({ children, ...props }: BaseComponentProps) => {
      // Check if this pre contains a code element with SyntaxHighlighter
      const hasCodeBlock = React.isValidElement(children) && 
        children.props && 
        typeof children.props === 'object' &&
        'className' in children.props &&
        typeof children.props.className === 'string' &&
        children.props.className.includes('language-');
      
      if (hasCodeBlock) {
        // If it's a code block, return the children directly (they're already wrapped in our custom div)
        return <>{children}</>;
      }
      
      // For regular pre elements, use standard styling
      return (
        <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm font-mono" {...props}>
          {children}
        </pre>
      );
    },
    h1: ({ children, ...props }: BaseComponentProps) => (
      <h1 className="text-lg font-bold mb-4 mt-6 text-gray-900" {...props}>
        {children}
      </h1>
    ),
    h2: ({ children, ...props }: BaseComponentProps) => (
      <h2 className="text-base font-semibold mb-3 mt-5 text-gray-900" {...props}>
        {children}
      </h2>
    ),
    h3: ({ children, ...props }: BaseComponentProps) => (
      <h3 className="text-sm font-semibold mb-2 mt-4 text-gray-900" {...props}>
        {children}
      </h3>
    ),
    h4: ({ children, ...props }: BaseComponentProps) => (
      <h4 className="text-sm font-medium mb-2 mt-3 text-gray-900" {...props}>
        {children}
      </h4>
    ),
    h5: ({ children, ...props }: BaseComponentProps) => (
      <h5 className="text-sm font-medium mb-2 mt-3 text-gray-900" {...props}>
        {children}
      </h5>
    ),
    h6: ({ children, ...props }: BaseComponentProps) => (
      <h6 className="text-sm font-medium mb-2 mt-3 text-gray-900" {...props}>
        {children}
      </h6>
    ),
    blockquote: ({ children, ...props }: BaseComponentProps) => (
      <blockquote className="border-l-4 border-gray-300 pl-4 my-4 italic text-gray-700" {...props}>
        {children}
      </blockquote>
    ),
    strong: ({ children, ...props }: BaseComponentProps) => (
      <strong className="font-semibold text-gray-900" {...props}>
        {children}
      </strong>
    ),
    em: ({ children, ...props }: BaseComponentProps) => (
      <em className="italic" {...props}>
        {children}
      </em>
    ),
    img: ({ src, alt, ...props }: BaseComponentProps & { src?: string | Blob; alt?: string }) => {
      // Don't render if src is empty or null
      if (!src || (typeof src === 'string' && src.trim() === '')) {
        return null;
      }
      const srcValue = typeof src === 'string' ? src : URL.createObjectURL(src);
      return (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={srcValue} alt={alt || ''} className="max-w-full h-auto rounded my-4" {...props} />
      );
    },
  };