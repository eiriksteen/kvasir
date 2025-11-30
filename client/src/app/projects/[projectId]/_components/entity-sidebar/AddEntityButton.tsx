'use client';

import React, { useState } from 'react';
import { Database, Plus, BarChart3, Zap, Folder, Brain } from 'lucide-react';
import { UUID } from 'crypto';
import { EntityType } from '@/types/ontology/entity-graph';
import { getEntityColorClasses } from '@/lib/entityColors';
import AddDataSource from '@/app/projects/[projectId]/_components/add-entity-modals/AddDataSource';
import AddAnalysis from '@/app/projects/[projectId]/_components/add-entity-modals/AddAnalysis';
import AddDataset from '@/app/projects/[projectId]/_components/add-entity-modals/AddDataset';
import AddPipeline from '@/app/projects/[projectId]/_components/add-entity-modals/AddPipeline';
import AddModelInstantiated from '@/app/projects/[projectId]/_components/add-entity-modals/AddModelEntity';

interface AddEntityButtonProps {
    type: EntityType;
    size?: number;
    projectId: UUID;
}

const getIcon = (type: EntityType, size: number) => {
    switch (type) {
        case 'dataset':
            return <Folder size={size} />;
        case 'data_source':
            return <Database size={size} />;
        case 'analysis':
            return <BarChart3 size={size} />;
        case 'pipeline':
            return <Zap size={size} />;
        case 'model_instantiated':
            return <Brain size={size} />;
    }
};

export default function AddEntityButton({ type, size = 11, projectId }: AddEntityButtonProps) {
    const [showModal, setShowModal] = useState(false);

    const handleClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        setShowModal(true);
    };

    const handleClose = () => {
        setShowModal(false);
    };
    
    const colors = getEntityColorClasses(type);
    const icon = getIcon(type, size);
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
                return <AddModelInstantiated onClose={handleClose} projectId={projectId} />;
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
                        {icon}
                        <div className={`${badgeClass} ${colors.plusBg} border ${colors.plusBorder}`}>
                            <Plus size={size * 0.35} className="text-white" />
                        </div>
                    </div>
                </div>
            </button>
            {renderModal()}
        </>
    );
}

