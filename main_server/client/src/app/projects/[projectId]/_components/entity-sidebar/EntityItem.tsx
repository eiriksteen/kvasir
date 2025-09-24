'use client';

import React from 'react';
import { Database, BarChart3, Zap, Folder } from 'lucide-react';
import { Dataset } from '@/types/data-objects';
import { Pipeline } from '@/types/pipeline';
import { AnalysisJobResultMetadata } from '@/types/analysis';
import { ModelEntity } from '@/types/model';

type ItemType = 'dataset' | 'analysis' | 'pipeline' | 'model_entity';

interface EntityItemProps {
    item: Dataset | AnalysisJobResultMetadata | Pipeline | ModelEntity;
    type: ItemType;
    isInContext: boolean;
    onClick: () => void;
}

export default function EntityItem({ item, type, isInContext, onClick }: EntityItemProps) {
    const getTheme = (type: ItemType) => {
        switch (type) {
            case 'model_entity':
                return {
                    bg: isInContext ? 'bg-[#491A32]/20' : 'hover:bg-[#491A32]/10',
                    icon: <Database size={11} />,
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
        }
    };

    const theme = getTheme(type);

    return (
        <div
            onClick={onClick}
            className={`group relative flex items-center gap-2 px-3 py-1.5 text-sm cursor-pointer transition-all duration-150 ${theme.bg} ${theme.hover}`}
        >
            <div className={`flex-shrink-0 ${theme.iconColor}`}>
                {theme.icon}
            </div>
            <span className={`truncate ${theme.textColor} font-mono text-xs`}>{item.name}</span>
        </div>
    );
}