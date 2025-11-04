'use client';

import React from 'react';
import { Brain, BarChart3, Zap, Folder, Database } from 'lucide-react';
import { Dataset } from '@/types/data-objects';
import { Pipeline } from '@/types/pipeline';
import { AnalysisSmall } from '@/types/analysis';
import { ModelEntity } from '@/types/model';
import { DataSource } from '@/types/data-sources';

type ItemType = 'dataset' | 'analysis' | 'pipeline' | 'model_entity' | 'data_source';

interface EntityItemProps {
    item: Dataset | AnalysisSmall | Pipeline | ModelEntity | DataSource;
    type: ItemType;
    isInContext: boolean;
    onClick: () => void;
    onOpenTab: () => void;
}

export default function EntityItem({ item, type, isInContext, onClick, onOpenTab }: EntityItemProps) {
    const getTheme = (type: ItemType) => {
        switch (type) {
            case 'model_entity':
                return {
                    bg: isInContext ? 'bg-[#491A32]/20' : 'hover:bg-[#491A32]/10',
                    icon: <Brain size={11} />,
                    iconColor: 'text-[#491A32]',
                    textColor: 'text-gray-800',
                    hover: 'hover:bg-[#491A32]/20'
                };
            case 'dataset':
                return {
                    bg: isInContext ? 'bg-[#0E4F70]/20' : 'hover:bg-[#0E4F70]/10',
                    icon: <Folder size={11} />,
                    iconColor: 'text-[#0E4F70]',
                    textColor: 'text-gray-800',
                    hover: 'hover:bg-[#0E4F70]/20'
                };
            case 'analysis':
                return {
                    bg: isInContext ? 'bg-[#004806]/20' : 'hover:bg-[#004806]/10',
                    icon: <BarChart3 size={11} />,
                    iconColor: 'text-[#004806]',
                    textColor: 'text-gray-800',
                    hover: 'hover:bg-[#004806]/20'
                };
            case 'pipeline':
                return {
                    bg: isInContext ? 'bg-[#840B08]/20' : 'hover:bg-[#840B08]/10',
                    icon: <Zap size={11} />,
                    iconColor: 'text-[#840B08]',
                    textColor: 'text-gray-800',
                    hover: 'hover:bg-[#840B08]/20'
                };
            case 'data_source':
                return {
                    bg: isInContext ? 'bg-gray-200' : 'hover:bg-gray-100',
                    icon: <Database size={11} />,
                    iconColor: 'text-gray-600',
                    textColor: 'text-gray-800',
                    hover: 'hover:bg-gray-200'
                };
        }
    };

    const theme = getTheme(type);

    const handleClick = (event: React.MouseEvent) => {
        if (event.metaKey || event.ctrlKey) {
            // Cmd+click or Ctrl+click - add to context
            onClick();
        } else {
            // Regular click - open tab
            onOpenTab();
        }
    };

    return (
        <div
            onClick={handleClick}
            className={`group relative flex items-center gap-2 px-3 py-1 text-sm cursor-pointer transition-all duration-150 ${theme.bg} ${theme.hover}`}
        >
            <div className={`flex-shrink-0 ${theme.iconColor}`}>
                {theme.icon}
            </div>
            <span className={`truncate ${theme.textColor} font-mono text-xs`}>{item.name}</span>
        </div>
    );
}