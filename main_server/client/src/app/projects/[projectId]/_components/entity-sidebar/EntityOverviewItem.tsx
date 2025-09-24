'use client';

import React from 'react';
import AddEntityButton from '@/app/projects/[projectId]/_components/entity-sidebar/AddEntityButton';

type ItemType = 'dataset' | 'analysis' | 'pipeline' | 'data_source' | 'model_entity';

interface EntityOverviewItemProps {
    title: string;
    count: number;
    color: 'blue' | 'purple' | 'orange' | 'emerald';
    onToggle: () => void;
    onAdd: () => void;
}

export default function EntityOverviewItem({ title, count, color, onToggle, onAdd }: EntityOverviewItemProps) {
    const getColorClasses = (color: 'blue' | 'purple' | 'orange' | 'emerald') => {
        switch (color) {
            case 'blue':
                return {
                    bg: 'bg-blue-50',
                    border: 'border-blue-200',
                    text: 'text-gray-700',
                    icon: 'text-blue-600',
                    hover: 'hover:bg-blue-100',
                    buttonHover: 'hover:bg-blue-200',
                    buttonBg: 'bg-blue-100',
                };
            case 'purple':
                return {
                    bg: 'bg-purple-50',
                    border: 'border-purple-200',
                    text: 'text-gray-700',
                    icon: 'text-purple-600',
                    hover: 'hover:bg-purple-100',
                    buttonHover: 'hover:bg-purple-200',
                    buttonBg: 'bg-purple-100',
                };
            case 'orange':
                return {
                    bg: 'bg-orange-50',
                    border: 'border-orange-200',
                    text: 'text-gray-700',
                    icon: 'text-orange-600',
                    hover: 'hover:bg-orange-100',
                    buttonHover: 'hover:bg-orange-200',
                    buttonBg: 'bg-orange-100',
                };
            case 'emerald':
                return {
                    bg: 'bg-emerald-50',
                    border: 'border-emerald-200',
                    text: 'text-gray-700',
                    icon: 'text-emerald-600',
                    hover: 'hover:bg-emerald-100',
                    buttonHover: 'hover:bg-emerald-200',
                    buttonBg: 'bg-emerald-100',
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
            className={`flex items-center justify-between px-3 py-2 cursor-pointer transition-colors ${colors.hover}`}
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

            <div className={colors.icon}>
                <AddEntityButton type={itemType} onAdd={onAdd} />
            </div>
        </div>
    );
}