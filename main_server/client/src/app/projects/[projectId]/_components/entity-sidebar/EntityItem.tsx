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
                    bg: isInContext ? 'bg-emerald-100' : 'hover:bg-emerald-50',
                    icon: <Database size={11} />,
                    iconColor: 'text-emerald-600',
                    textColor: 'text-gray-800',
                    hover: 'hover:bg-emerald-100'
                };
            case 'dataset':
                return {
                    bg: isInContext ? 'bg-blue-100' : 'hover:bg-blue-50',
                    icon: <Folder size={11} />,
                    iconColor: 'text-blue-600',
                    textColor: 'text-gray-800',
                    hover: 'hover:bg-blue-100'
                };
            case 'analysis':
                return {
                    bg: isInContext ? 'bg-purple-100' : 'hover:bg-purple-50',
                    icon: <BarChart3 size={11} />,
                    iconColor: 'text-purple-600',
                    textColor: 'text-gray-800',
                    hover: 'hover:bg-purple-100'
                };
            case 'pipeline':
                return {
                    bg: isInContext ? 'bg-orange-100' : 'hover:bg-orange-50',
                    icon: <Zap size={11} />,
                    iconColor: 'text-orange-600',
                    textColor: 'text-gray-800',
                    hover: 'hover:bg-orange-100'
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