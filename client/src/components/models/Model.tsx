'use client';

import ModelMini from './ModelMini';
import ModelCompact from './ModelCompact';
import { useState } from 'react';
import ModelFull from './ModelFull';
import { useModels } from '@/hooks/useModels';
import { Handle, Position } from '@xyflow/react';
import { createPortal } from 'react-dom';

interface ModelProps {
  modelId: string;
  gradientClass: string;
  defaultView: 'mini' | 'compact' | 'full';
}

export default function Model({ modelId, gradientClass, defaultView }: ModelProps) {

  const [currentView, setCurrentView] = useState<ModelProps['defaultView']>(defaultView);
  const { models } = useModels();
  const model = models?.find(m => m.id === modelId);

  if (!model) return null;

  return (
    <div>
    {currentView === 'mini' && <ModelMini model={model} gradientClass={gradientClass} onClick={() => setCurrentView('full')}/>}
    {currentView === 'compact' && <ModelCompact model={model} gradientClass={gradientClass} onClick={() => setCurrentView('full')}/>}
    {currentView === 'full' && createPortal(
      <ModelFull 
        model={model} 
        gradientClass={gradientClass} 
        onClose={() => setCurrentView(defaultView)} 
      />,
      document.body
    )}
    <Handle type="source" position={Position.Right} style={{ background: '#6366f1' }} />
    </div>
  );
} 