'use client';

import React, { useState } from 'react';
import { useCodebaseTree } from "@/hooks/useCodebase";
import { UUID } from "crypto";
import { ProjectPath } from "@/types/code";
import { ChevronRight, ChevronDown, File, Folder, FolderOpen } from 'lucide-react';
import CodeViewer from '@/components/code/CodeViewer';

interface CodebaseTreeProps {
    projectId: UUID;
}

interface FileTreeItemProps {
    node: ProjectPath;
    depth: number;
    parentPath: string;
    onFileClick: (fullPath: string) => void;
}

const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase();
    const iconClass = "flex-shrink-0";
    
    const colorMap: Record<string, string> = {
        'py': 'text-blue-600',
        'js': 'text-yellow-500',
        'jsx': 'text-blue-500',
        'ts': 'text-blue-600',
        'tsx': 'text-blue-500',
        'json': 'text-yellow-600',
        'yaml': 'text-purple-500',
        'yml': 'text-purple-500',
        'md': 'text-gray-700',
        'csv': 'text-green-600',
        'txt': 'text-gray-500',
        'sh': 'text-green-700',
        'sql': 'text-orange-600',
        'html': 'text-orange-500',
        'css': 'text-blue-400',
    };
    
    const color = colorMap[ext || ''] || 'text-gray-600';
    return <File size={11} className={`${iconClass} ${color}`} />;
};

function FileTreeItem({ node, depth, parentPath, onFileClick }: FileTreeItemProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const isDirectory = !node.isFile;
    const fullPath = parentPath ? `${parentPath}/${node.path}` : node.path;
    
    const handleClick = () => {
        if (isDirectory) {
            setIsExpanded(!isExpanded);
        } else {
            onFileClick(fullPath);
        }
    };

    return (
        <div>
            <div
                onClick={handleClick}
                className="group relative flex items-center gap-1.5 py-1 text-sm cursor-pointer hover:bg-gray-100 transition-all duration-150"
                style={{ paddingLeft: `${depth * 10 + 8}px` }}
            >
                {isDirectory ? (
                    <>
                        {isExpanded ? (
                            <ChevronDown size={12} className="flex-shrink-0 text-gray-500" />
                        ) : (
                            <ChevronRight size={12} className="flex-shrink-0 text-gray-500" />
                        )}
                        {isExpanded ? (
                            <FolderOpen size={11} className="flex-shrink-0 text-gray-600" />
                        ) : (
                            <Folder size={11} className="flex-shrink-0 text-gray-600" />
                        )}
                    </>
                ) : (
                    <>
                        <span className="w-3" />
                        {getFileIcon(node.path)}
                    </>
                )}
                <span className="truncate text-gray-800 font-mono text-xs">{node.path}</span>
            </div>
            
            {isDirectory && isExpanded && node.subPaths.map((subNode, idx) => (
                <FileTreeItem
                    key={`${fullPath}/${subNode.path}-${idx}`}
                    node={subNode}
                    depth={depth + 1}
                    parentPath={fullPath}
                    onFileClick={onFileClick}
                />
            ))}
        </div>
    );
}

export default function CodebaseTree({ projectId }: CodebaseTreeProps) {
    const { codebaseTree, isLoading } = useCodebaseTree(projectId);
    const [selectedFile, setSelectedFile] = useState<string | null>(null);

    const handleFileClick = (filePath: string) => {
        setSelectedFile(filePath);
    };

    if (isLoading) {
        return (
            <div className="px-3 py-4 text-center">
                <p className="text-xs text-gray-500">Loading codebase...</p>
            </div>
        );
    }

    if (!codebaseTree) {
        return (
            <div className="px-3 py-4 text-center">
                <p className="text-xs text-gray-500">No codebase found</p>
            </div>
        );
    }

    return (
        <>
            <div>
                {codebaseTree.subPaths.map((subNode, idx) => (
                    <FileTreeItem
                        key={`${subNode.path}-${idx}`}
                        node={subNode}
                        depth={0}
                        parentPath=""
                        onFileClick={handleFileClick}
                    />
                ))}
            </div>
            
            {selectedFile && (
                <CodeViewer
                    projectId={projectId}
                    filePath={selectedFile}
                    onClose={() => setSelectedFile(null)}
                />
            )}
        </>
    );
}