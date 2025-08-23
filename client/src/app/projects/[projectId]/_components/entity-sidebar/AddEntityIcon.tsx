'use client';
import React from 'react';

import { Database, Plus, BarChart3, Zap, Folder } from 'lucide-react';

type ItemType = 'dataset' | 'analysis' | 'pipeline' | 'data_source';

// Component for merged concept + plus icons
export default function AddEntityIcon({ type, size = 13 }: { type: ItemType; size?: number }) {
    const badgeClass = "absolute top-[-8px] right-[-8px] rounded-full p-0.5 z-10";
    const getIcon = () => {
        switch (type) {
            case 'data_source':
                return (
                    <div className="relative overflow-visible">
                        <Database size={size} />
                        <div className={badgeClass + " bg-emerald-500 border border-emerald-400/30"}>
                            <Plus size={size * 0.35} className="text-white" />
                        </div>
                    </div>
                );
            case 'dataset':
                return (
                    <div className="relative overflow-visible">
                        <Folder size={size} />
                        <div className={badgeClass + " bg-blue-500 border border-blue-400/30"}>
                            <Plus size={size * 0.35} className="text-white" />
                        </div>
                    </div>
                );
            case 'analysis':
                return (
                    <div className="relative overflow-visible">
                        <BarChart3 size={size} />
                        <div className={badgeClass + " bg-purple-500 border border-purple-400/30"}>
                            <Plus size={size * 0.35} className="text-white" />
                        </div>
                    </div>
                );
            case 'pipeline':
                return (
                    <div className="relative overflow-visible">
                        <Zap size={size} />
                        <div className={badgeClass + " bg-orange-500 border border-orange-400/30"}>
                            <Plus size={size * 0.35} className="text-white" />
                        </div>
                    </div>
                );
        }
    };

    return getIcon();
}