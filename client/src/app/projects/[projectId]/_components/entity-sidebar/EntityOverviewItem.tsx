'use client';

import React from 'react';
import AddEntityIcon from '@/app/projects/[projectId]/_components/entity-sidebar/AddEntityIcon';

type ItemType = 'dataset' | 'analysis' | 'automation' | 'data_source';

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
                    bg: 'bg-blue-500/20',
                    border: 'border-blue-400/50',
                    text: 'text-gray-300',
                    icon: 'text-blue-300',
                    hover: 'hover:bg-blue-500/30',
                    buttonHover: 'hover:bg-blue-500/40',
                    buttonBg: 'bg-blue-500/15',
                };
            case 'purple':
                return {
                    bg: 'bg-purple-500/20',
                    border: 'border-purple-400/50',
                    text: 'text-gray-300',
                    icon: 'text-purple-300',
                    hover: 'hover:bg-purple-500/30',
                    buttonHover: 'hover:bg-purple-500/40',
                    buttonBg: 'bg-purple-500/15',
                };
            case 'orange':
                return {
                    bg: 'bg-orange-500/20',
                    border: 'border-orange-400/50',
                    text: 'text-gray-300',
                    icon: 'text-orange-300',
                    hover: 'hover:bg-orange-500/30',
                    buttonHover: 'hover:bg-orange-500/40',
                    buttonBg: 'bg-orange-500/15',
                };
            case 'emerald':
                return {
                    bg: 'bg-emerald-500/20',
                    border: 'border-emerald-400/50',
                    text: 'text-gray-300',
                    icon: 'text-emerald-300',
                    hover: 'hover:bg-emerald-500/30',
                    buttonHover: 'hover:bg-emerald-500/40',
                    buttonBg: 'bg-emerald-500/15',
                };
        }
    };

    const colors = getColorClasses(color);
    const itemTypeMap: Record<string, ItemType> = {
        'Datasets': 'dataset',
        'Analysis': 'analysis',
        'Automations': 'automation',
        'Data Sources': 'data_source'
    };
    const itemType = itemTypeMap[title];

    return (
        <div 
            className={`flex items-center justify-between px-3 py-2 cursor-pointer transition-colors ${colors.hover}`}
            onClick={onToggle}
        >
            <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-gray-400 bg-gray-800/50 px-1.5 py-0.5 rounded">
                    {count}
                </span>
                <span className={`text-xs font-mono ${colors.text}`}>
                    {title}
                </span>
            </div>
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    onAdd();
                }}
                className={`p-1.5 rounded-md inline-flex items-center justify-center min-w-[32px] min-h-[32px] ${colors.buttonBg} border ${colors.border} transition-all duration-200 ${colors.buttonHover} hover:scale-105`}
                title={`Add ${title.slice(0, -1)}`}
            >
                <div className={colors.icon}>
                    <AddEntityIcon type={itemType} />
                </div>
            </button>
        </div>
    );
}