'use client';

import React from 'react';
import { UUID } from 'crypto';
import { useCodebaseFile } from '@/hooks/useCodebase';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { X, FileCode } from 'lucide-react';

interface CodeViewerProps {
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

export default function CodeViewer({ projectId, filePath, onClose }: CodeViewerProps) {
    const { fileContent, isLoading, error } = useCodebaseFile(projectId, filePath);

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
            <div 
                className="bg-white rounded-lg shadow-xl w-[90%] h-[90%] flex flex-col"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
                    <div className="flex items-center gap-2">
                        <FileCode size={16} className="text-gray-600" />
                        <h2 className="text-sm font-mono text-gray-800">{filePath}</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1 hover:bg-gray-200 rounded transition-colors"
                    >
                        <X size={16} className="text-gray-600" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-auto bg-gray-50">
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
                        <div className="p-4">
                            <div className="rounded-lg overflow-hidden border border-gray-200 bg-white">
                                <SyntaxHighlighter
                                    style={oneLight}
                                    language={getLanguageFromPath(filePath)}
                                    showLineNumbers
                                    PreTag="div"
                                    customStyle={{
                                        margin: 0,
                                        background: 'white',
                                        fontSize: '0.75rem',
                                        padding: '1rem',
                                    }}
                                >
                                    {String(fileContent)}
                                </SyntaxHighlighter>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

