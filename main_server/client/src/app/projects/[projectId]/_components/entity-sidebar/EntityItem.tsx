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
                    bg: isInContext ? 'bg-emerald-500/10' : 'hover:bg-emerald-500/5',
                    icon: <Database size={11} />,
                    iconColor: 'text-emerald-400',
                    textColor: 'text-gray-200',
                    hover: 'hover:bg-emerald-500/8'
                };
            case 'dataset':
                return {
                    bg: isInContext ? 'bg-blue-500/10' : 'hover:bg-blue-500/5',
                    icon: <Folder size={11} />,
                    iconColor: 'text-blue-400',
                    textColor: 'text-gray-200',
                    hover: 'hover:bg-blue-500/8'
                };
            case 'analysis':
                return {
                    bg: isInContext ? 'bg-purple-500/10' : 'hover:bg-purple-500/5',
                    icon: <BarChart3 size={11} />,
                    iconColor: 'text-purple-400',
                    textColor: 'text-gray-200',
                    hover: 'hover:bg-purple-500/8'
                };
            case 'pipeline':
                return {
                    bg: isInContext ? 'bg-orange-500/10' : 'hover:bg-orange-500/5',
                    icon: <Zap size={11} />,
                    iconColor: 'text-orange-400',
                    textColor: 'text-gray-200',
                    hover: 'hover:bg-orange-500/8'
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