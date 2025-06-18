import React from 'react';
import { BaseEdge, getStraightPath } from '@xyflow/react';

const TransportEdge = ({ id, sourceX, sourceY, targetX, targetY }: {
  id: string;
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
}) => {
  const [edgePath] = getStraightPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
  });

  return (
    <>
      <BaseEdge 
        id={id} 
        path={edgePath} 
        style={{ stroke: '#6366f1', strokeWidth: 2 }} 
      />
    </>
  );
};

export default TransportEdge;
