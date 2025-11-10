'use client';

import React from 'react';
import AddEntityButton from '@/app/projects/[projectId]/_components/entity-sidebar/AddEntityButton';
import { UUID } from 'crypto';

type ItemType = 'dataset' | 'analysis' | 'pipeline' | 'data_source' | 'model_entity';

interface EntityOverviewItemProps {
    title: string;
    count: number;
    color: 'blue' | 'purple' | 'orange' | 'emerald';
    onToggle: () => void;
    projectId: UUID;
}

export default function EntityOverviewItem({ title, count, color, onToggle, projectId }: EntityOverviewItemProps) {
    const getColorClasses = (color: 'blue' | 'purple' | 'orange' | 'emerald') => {
        switch (color) {
            case 'blue':
                return {
                    bg: 'bg-[#0E4F70]/10',
                    border: 'border-[#0E4F70]/20',
                    text: 'text-gray-700',
                    icon: 'text-[#0E4F70]',
                    hover: 'hover:bg-[#0E4F70]/20',
                    buttonHover: 'hover:bg-[#0E4F70]/30',
                    buttonBg: 'bg-[#0E4F70]/20',
                };
            case 'purple':
                return {
                    bg: 'bg-[#004806]/10',
                    border: 'border-[#004806]/20',
                    text: 'text-gray-700',
                    icon: 'text-[#004806]',
                    hover: 'hover:bg-[#004806]/20',
                    buttonHover: 'hover:bg-[#004806]/30',
                    buttonBg: 'bg-[#004806]/20',
                };
            case 'orange':
                return {
                    bg: 'bg-[#840B08]/10',
                    border: 'border-[#840B08]/20',
                    text: 'text-gray-700',
                    icon: 'text-[#840B08]',
                    hover: 'hover:bg-[#840B08]/20',
                    buttonHover: 'hover:bg-[#840B08]/30',
                    buttonBg: 'bg-[#840B08]/20',
                };
            case 'emerald':
                return {
                    bg: 'bg-[#491A32]/10',
                    border: 'border-[#491A32]/20',
                    text: 'text-gray-700',
                    icon: 'text-[#491A32]',
                    hover: 'hover:bg-[#491A32]/20',
                    buttonHover: 'hover:bg-[#491A32]/30',
                    buttonBg: 'bg-[#491A32]/20',
                };
        }
    };

    const colors = getColorClasses(color);
    const itemTypeMap: Record<string, ItemType> = {
        'Datasets': 'dataset',
        'Analyses': 'analysis',
        'Pipelines': 'pipeline',
        'Data Sources': 'data_source',
        'Models': 'model_entity',
    };
    const itemType = itemTypeMap[title];

    return (
        <div 
            className={`flex items-center justify-between px-3 py-1 cursor-pointer transition-colors ${colors.hover}`}
            onClick={onToggle}
        >
            <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-gray-600 bg-gray-200 px-1.5 py-0.5 rounded">
                    {count}
                </span>
                <span className={`text-xs font-mono ${colors.text}`}>
                    {title}
                </span>
            </div>

            <div className={colors.icon} onClick={(e) => e.stopPropagation()}>
                <AddEntityButton type={itemType} projectId={projectId} size={11} />
            </div>
        </div>
    );
}