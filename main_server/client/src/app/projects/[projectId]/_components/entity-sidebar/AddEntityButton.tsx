'use client';

import React from 'react';
import { Database, Plus, BarChart3, Zap, Folder, Brain } from 'lucide-react';

type ItemType = 'dataset' | 'analysis' | 'pipeline' | 'data_source' | 'model_entity';

interface AddEntityButtonProps {
    type: ItemType;
    size?: number;
    onAdd: () => void;
}

interface Style {
    bg: string;
    border: string;
    text: string;
    icon: string;
    hover: string;
    buttonHover: string;
    buttonBg: string;
    plusBg: string;
    plusBorder: string;
    symbol: React.ReactNode;
}


export default function AddEntityButton({ type, size = 13, onAdd }: AddEntityButtonProps) {
    const getStyleFromType = (type: 'dataset' | 'analysis' | 'pipeline' | 'data_source' | 'model_entity'): Style => {
        switch (type) {
            case 'dataset':
                return {
                    bg: 'bg-blue-500/20',
                    border: 'border-blue-400/50',
                    text: 'text-gray-300',
                    icon: 'text-blue-300',
                    hover: 'hover:bg-blue-500/30',
                    buttonHover: 'hover:bg-blue-500/40',
                    buttonBg: 'bg-blue-500/15',
                    plusBg: 'bg-blue-500',
                    plusBorder: 'border-blue-400/30',
                    symbol: <Folder size={size} />,
                };
            case 'data_source':
                return {
                    bg: 'bg-gray-600/20',
                    border: 'border-gray-400/50',
                    text: 'text-gray-300',
                    icon: 'text-gray-300',
                    hover: 'hover:bg-gray-600/30',
                    buttonHover: 'hover:bg-gray-600/40',
                    buttonBg: 'bg-gray-600/15',
                    plusBg: 'bg-gray-500',
                    plusBorder: 'border-gray-400/30',
                    symbol: <Database size={size} />,
                };
            case 'analysis':
                return {
                    bg: 'bg-purple-500/20',
                    border: 'border-purple-400/50',
                    text: 'text-gray-300',
                    icon: 'text-purple-300',
                    hover: 'hover:bg-purple-500/30',
                    buttonHover: 'hover:bg-purple-500/40',
                    buttonBg: 'bg-purple-500/15',
                    plusBg: 'bg-purple-500',
                    plusBorder: 'border-purple-400/30',
                    symbol: <BarChart3 size={size} />,
                };
            case 'pipeline':
                return {
                    bg: 'bg-orange-500/20',
                    border: 'border-orange-400/50',
                    text: 'text-gray-300',
                    icon: 'text-orange-300',
                    hover: 'hover:bg-orange-500/30',
                    buttonHover: 'hover:bg-orange-500/40',
                    buttonBg: 'bg-orange-500/15',
                    plusBg: 'bg-orange-500',
                    plusBorder: 'border-orange-400/30',
                    symbol: <Zap size={size} />,

                };
            case 'model_entity':
                return {
                    bg: 'bg-emerald-500/20',
                    border: 'border-emerald-400/50',
                    text: 'text-gray-300',
                    icon: 'text-emerald-300',
                    hover: 'hover:bg-emerald-500/30',
                    buttonHover: 'hover:bg-emerald-500/40',
                    buttonBg: 'bg-emerald-500/15',
                    plusBg: 'bg-emerald-500',
                    plusBorder: 'border-emerald-400/30',
                    symbol: <Brain size={size} />,
                };
            }
        };

        const colors = getStyleFromType(type);
        const badgeClass = "absolute top-[-8px] right-[-8px] rounded-full p-0.5 z-10";

        return (
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    onAdd();
                }}
                className={`p-1.5 rounded-md inline-flex items-center justify-center min-w-[32px] min-h-[32px] ${colors.buttonBg} ${colors.border} transition-all duration-200 ${colors.buttonHover} hover:scale-105`}
                title={`Add ${type.slice(0, -1)}`}
            >
            <div className={colors.icon}>
                <div className="relative overflow-visible">
                    {colors.symbol}
                    <div className={badgeClass + " " + colors.plusBg + " border " + colors.plusBorder}>
                        <Plus size={size * 0.35} className="text-white" />
                    </div>
                    </div>
                </div>
            </button>
        );
    };

