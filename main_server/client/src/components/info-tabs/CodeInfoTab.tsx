'use client';

import React, { useEffect } from 'react';
import { UUID } from 'crypto';
import { useCodebaseFile } from '@/hooks/useCodebase';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface CodeInfoTabProps {
    projectId: UUID;
    filePath: string;
    onClose: () => void;
}

const getLanguageFromPath = (path: string): string => {
    const ext = path.split('.').pop()?.toLowerCase();
    const langMap: Record<string, string> = {
        'py': 'python',
        'js': 'javascript',
        'jsx': 'jsx',
        'ts': 'typescript',
        'tsx': 'tsx',
        'json': 'json',
        'yaml': 'yaml',
        'yml': 'yaml',
        'md': 'markdown',
        'csv': 'csv',
        'txt': 'text',
        'sh': 'bash',
        'sql': 'sql',
        'html': 'html',
        'css': 'css',
        'xml': 'xml',
        'toml': 'toml',
        'ini': 'ini',
    };
    return langMap[ext || ''] || 'text';
};

export default function CodeInfoTab({ projectId, filePath, onClose }: CodeInfoTabProps) {
    const { fileContent, isLoading, error } = useCodebaseFile(projectId, filePath);

    // Handle escape key to close tab and return to project view
    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                e.preventDefault();
                e.stopPropagation();
                onClose();
            }
        };

        document.addEventListener('keydown', handleEscape, { capture: true });
        return () => document.removeEventListener('keydown', handleEscape, { capture: true });
    }, [onClose]);

    return (
        <div className="flex flex-col h-full bg-white">
            {/* Content */}
            <div className="flex-1 overflow-auto">
                {isLoading && (
                    <div className="flex items-center justify-center h-full">
                        <p className="text-sm text-gray-500">Loading file...</p>
                    </div>
                )}
                
                {error && (
                    <div className="flex items-center justify-center h-full">
                        <p className="text-sm text-red-500">Error loading file: {error.message}</p>
                    </div>
                )}
                
                {fileContent && (
                    <div className="w-full">
                        <SyntaxHighlighter
                            style={oneLight}
                            language={getLanguageFromPath(filePath)}
                            showLineNumbers
                            PreTag="div"
                            wrapLongLines={false}
                            lineNumberStyle={{
                                minWidth: '3.5em',
                                paddingRight: '1em',
                                textAlign: 'right',
                                userSelect: 'none',
                            }}
                            customStyle={{
                                margin: 0,
                                background: 'white',
                                fontSize: '0.75rem',
                                padding: '1rem',
                                width: '100%',
                            }}
                        >
                            {String(fileContent)}
                        </SyntaxHighlighter>
                    </div>
                )}
            </div>
        </div>
    );
}

