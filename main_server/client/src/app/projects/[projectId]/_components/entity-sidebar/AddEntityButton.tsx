'use client';

import React, { useState } from 'react';
import { Database, Plus, BarChart3, Zap, Folder, Brain } from 'lucide-react';
import { UUID } from 'crypto';
import AddDataSource from '@/app/projects/[projectId]/_components/add-entity-modals/AddDataSource';
import AddAnalysis from '@/app/projects/[projectId]/_components/add-entity-modals/AddAnalysis';
import AddDataset from '@/app/projects/[projectId]/_components/add-entity-modals/AddDataset';
import AddPipeline from '@/app/projects/[projectId]/_components/add-entity-modals/AddPipeline';
import AddModelEntity from '@/app/projects/[projectId]/_components/add-entity-modals/AddModelEntity';

type ItemType = 'dataset' | 'analysis' | 'pipeline' | 'data_source' | 'model_instantiated';

interface AddEntityButtonProps {
    type: ItemType;
    size?: number;
    projectId: UUID;
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


export default function AddEntityButton({ type, size = 11, projectId }: AddEntityButtonProps) {
    const [showModal, setShowModal] = useState(false);

    const handleClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        setShowModal(true);
    };

    const handleClose = () => {
        setShowModal(false);
    };
    const getStyleFromType = (type: 'dataset' | 'analysis' | 'pipeline' | 'data_source' | 'model_instantiated'): Style => {
        switch (type) {
            case 'dataset':
                return {
                    bg: 'bg-[#0E4F70]/10',
                    border: 'border border-[#0E4F70]',
                    text: 'text-gray-700',
                    icon: 'text-[#0E4F70]',
                    hover: 'hover:bg-[#0E4F70]/20',
                    buttonHover: 'hover:bg-[#0E4F70]/30',
                    buttonBg: 'bg-[#0E4F70]/10',
                    plusBg: 'bg-[#0E4F70]',
                    plusBorder: 'border-[#0E4F70]/50',
                    symbol: <Folder size={size} />,
                };
            case 'data_source':
                return {
                    bg: 'bg-[#6b7280]/10',
                    border: 'border border-gray-600',
                    text: 'text-gray-700',
                    icon: 'text-gray-600',
                    hover: 'hover:bg-[#6b7280]/10',
                    buttonHover: 'hover:bg-[#6b7280]/20',
                    buttonBg: 'bg-[#6b7280]/10',
                    plusBg: 'bg-gray-600',
                    plusBorder: 'border-gray-300',
                    symbol: <Database size={size} />,
                };
            case 'analysis':
                return {
                    bg: 'bg-[#004806]/10',
                    border: 'border border-[#004806]',
                    text: 'text-gray-700',
                    icon: 'text-[#004806]',
                    hover: 'hover:bg-[#004806]/20',
                    buttonHover: 'hover:bg-[#004806]/30',
                    buttonBg: 'bg-[#004806]/10',
                    plusBg: 'bg-[#004806]',
                    plusBorder: 'border-[#004806]/50',
                    symbol: <BarChart3 size={size} />,
                };
            case 'pipeline':
                return {
                    bg: 'bg-[#840B08]/10',
                    border: 'border border-[#840B08]',
                    text: 'text-gray-700',
                    icon: 'text-[#840B08]',
                    hover: 'hover:bg-[#840B08]/20',
                    buttonHover: 'hover:bg-[#840B08]/30',
                    buttonBg: 'bg-[#840B08]/10',
                    plusBg: 'bg-[#840B08]',
                    plusBorder: 'border-[#840B08]/50',
                    symbol: <Zap size={size} />,

                };
            case 'model_instantiated':
                return {
                    bg: 'bg-[#491A32]/10',
                    border: 'border border-[#491A32]',
                    text: 'text-gray-700',
                    icon: 'text-[#491A32]',
                    hover: 'hover:bg-[#491A32]/20',
                    buttonHover: 'hover:bg-[#491A32]/30',
                    buttonBg: 'bg-[#491A32]/10',
                    plusBg: 'bg-[#491A32]',
                    plusBorder: 'border-[#491A32]/50',
                    symbol: <Brain size={size} />,
                };
            }
        };

        const colors = getStyleFromType(type);
        const badgeClass = "absolute top-[-8px] right-[-8px] rounded-full p-0.5 z-10";

        const renderModal = () => {
            if (!showModal) return null;
            
            switch (type) {
                case 'data_source':
                    return <AddDataSource onClose={handleClose} projectId={projectId} />;
                case 'dataset':
                    return <AddDataset onClose={handleClose} projectId={projectId} />;
                case 'analysis':
                    return <AddAnalysis onClose={handleClose} projectId={projectId} />;
                case 'pipeline':
                    return <AddPipeline onClose={handleClose} projectId={projectId} />;
                case 'model_instantiated':
                    return <AddModelEntity onClose={handleClose} projectId={projectId} />;
                default:
                    return null;
            }
        };

        return (
            <>
                <button
                    onClick={handleClick}
                    className={`p-1 rounded-md inline-flex items-center justify-center min-w-[14px] min-h-[14px] ${colors.buttonBg} ${colors.border} transition-all duration-200 ${colors.buttonHover} hover:scale-105`}
                    title={`Add ${type.replace('_', ' ')}`}
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
                {renderModal()}
            </>
        );
    };

