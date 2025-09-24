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
                    bg: 'bg-blue-50',
                    border: 'border-blue-600',
                    text: 'text-gray-700',
                    icon: 'text-blue-600',
                    hover: 'hover:bg-blue-100',
                    buttonHover: 'hover:bg-blue-200',
                    buttonBg: 'bg-blue-100',
                    plusBg: 'bg-blue-600',
                    plusBorder: 'border-blue-300',
                    symbol: <Folder size={size} />,
                };
            case 'data_source':
                return {
                    bg: 'bg-gray-50',
                    border: 'border-gray-600',
                    text: 'text-gray-700',
                    icon: 'text-gray-600',
                    hover: 'hover:bg-gray-100',
                    buttonHover: 'hover:bg-gray-200',
                    buttonBg: 'bg-gray-100',
                    plusBg: 'bg-gray-600',
                    plusBorder: 'border-gray-300',
                    symbol: <Database size={size} />,
                };
            case 'analysis':
                return {
                    bg: 'bg-purple-50',
                    border: 'border-purple-600',
                    text: 'text-gray-700',
                    icon: 'text-purple-600',
                    hover: 'hover:bg-purple-100',
                    buttonHover: 'hover:bg-purple-200',
                    buttonBg: 'bg-purple-100',
                    plusBg: 'bg-purple-600',
                    plusBorder: 'border-purple-300',
                    symbol: <BarChart3 size={size} />,
                };
            case 'pipeline':
                return {
                    bg: 'bg-orange-50',
                    border: 'border-orange-600',
                    text: 'text-gray-700',
                    icon: 'text-orange-600',
                    hover: 'hover:bg-orange-100',
                    buttonHover: 'hover:bg-orange-200',
                    buttonBg: 'bg-orange-100',
                    plusBg: 'bg-orange-600',
                    plusBorder: 'border-orange-300',
                    symbol: <Zap size={size} />,

                };
            case 'model_entity':
                return {
                    bg: 'bg-emerald-50',
                    border: 'border-emerald-600',
                    text: 'text-gray-700',
                    icon: 'text-emerald-600',
                    hover: 'hover:bg-emerald-100',
                    buttonHover: 'hover:bg-emerald-200',
                    buttonBg: 'bg-emerald-100',
                    plusBg: 'bg-emerald-600',
                    plusBorder: 'border-emerald-300',
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
                className={`p-1.5 rounded-md inline-flex items-center justify-center min-w-[32px] min-h-[32px] ${colors.buttonBg} border ${colors.border} transition-all duration-200 ${colors.buttonHover} hover:scale-105`}
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

