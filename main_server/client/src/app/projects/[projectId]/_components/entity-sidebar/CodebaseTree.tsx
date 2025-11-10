'use client';

import React, { useState } from 'react';
import { useCodebaseTree } from "@/hooks/useCodebase";
import { UUID } from "crypto";
import { ProjectPath } from "@/types/code";
import { ChevronRight, ChevronDown, File, Folder, FolderOpen } from 'lucide-react';
import { 
    SiPython, 
    SiJavascript, 
    SiTypescript, 
    SiReact,
    SiYaml,
    SiMarkdown,
    SiHtml5,
    SiCss3,
    SiShell,
} from 'react-icons/si';
import { VscJson, VscFile } from 'react-icons/vsc';

interface CodebaseTreeProps {
    projectId: UUID;
    onFileClick: (filePath: string) => void;
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
    const size = 11;
    
    switch (ext) {
        case 'py':
            return <SiPython size={size} className={`${iconClass} text-[#3776AB]`} />;
        case 'js':
            return <SiJavascript size={size} className={`${iconClass} text-[#F7DF1E]`} />;
        case 'jsx':
            return <SiReact size={size} className={`${iconClass} text-[#61DAFB]`} />;
        case 'ts':
            return <SiTypescript size={size} className={`${iconClass} text-[#3178C6]`} />;
        case 'tsx':
            return <SiReact size={size} className={`${iconClass} text-[#3178C6]`} />;
        case 'json':
            return <VscJson size={size} className={`${iconClass} text-[#6b7280]`} />;
        case 'yaml':
        case 'yml':
            return <SiYaml size={size} className={`${iconClass} text-[#6b7280]`} />;
        case 'md':
        case 'mdx':
            return <SiMarkdown size={size} className={`${iconClass} text-[#6b7280]`} />;
        case 'html':
            return <SiHtml5 size={size} className={`${iconClass} text-[#E34F26]`} />;
        case 'css':
            return <SiCss3 size={size} className={`${iconClass} text-[#1572B6]`} />;
        case 'sh':
        case 'bash':
            return <SiShell size={size} className={`${iconClass} text-[#4EAA25]`} />;
        case 'txt':
        case 'csv':
        case 'sql':
            return <VscFile size={size} className={`${iconClass} text-[#6b7280]`} />;
        default:
            return <File size={11} className={`${iconClass} text-[#6b7280]`} />;
    }
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
                            <ChevronDown size={12} className="flex-shrink-0 text-[#6b7280]" />
                        ) : (
                            <ChevronRight size={12} className="flex-shrink-0 text-[#6b7280]" />
                        )}
                        {isExpanded ? (
                            <FolderOpen size={11} className="flex-shrink-0 text-[#6b7280]" />
                        ) : (
                            <Folder size={11} className="flex-shrink-0 text-[#6b7280]" />
                        )}
                    </>
                ) : (
                    <>
                        <span className="w-3 flex-shrink-0" />
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

export default function CodebaseTree({ projectId, onFileClick }: CodebaseTreeProps) {
    const { codebaseTree, isLoading } = useCodebaseTree(projectId);

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
        <div>
            {codebaseTree.subPaths.map((subNode, idx) => (
                <FileTreeItem
                    key={`${subNode.path}-${idx}`}
                    node={subNode}
                    depth={0}
                    parentPath=""
                    onFileClick={onFileClick}
                />
            ))}
        </div>
    );
}