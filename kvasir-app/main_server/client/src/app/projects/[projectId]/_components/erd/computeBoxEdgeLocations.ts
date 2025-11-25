type EntityPosition = {
    xPosition: number;
    yPosition: number;
}

function sourceIsAboveTarget(sourceEntity: EntityPosition, targetEntity: EntityPosition) {
    return sourceEntity.yPosition < targetEntity.yPosition;
}

function sourceIsToTheRightOfTarget(sourceEntity: EntityPosition, targetEntity: EntityPosition) {
    return targetEntity.xPosition + 150 <= sourceEntity.xPosition;
}

function sourceIsBelowTarget(sourceEntity: EntityPosition, targetEntity: EntityPosition) {
    return sourceEntity.yPosition >= targetEntity.yPosition;
}

function sourceIsToTheLeftOfTarget(sourceEntity: EntityPosition, targetEntity: EntityPosition) {
    return sourceEntity.xPosition < targetEntity.xPosition - 150;
}

type Edge = {
    from: "left-source" | "right-source" | "bottom-source" | "top-source";
    to: "left-target" | "right-target" | "bottom-target" | "top-target";
}

export function computeBoxEdgeLocations(sourceEntity: EntityPosition, targetEntity: EntityPosition): Edge {
    if (sourceIsToTheRightOfTarget(sourceEntity, targetEntity)){
        return { from: "left-source", to: "right-target" };
    }
    else if (sourceIsToTheLeftOfTarget(sourceEntity, targetEntity)){
        return { from: "right-source", to: "left-target" };
    }
    else if (sourceIsBelowTarget(sourceEntity, targetEntity)){
        return { from: "top-source", to: "bottom-target" };
    }
    else if (sourceIsAboveTarget(sourceEntity, targetEntity)){
        return { from: "bottom-source", to: "top-target" };
    }
    else {
        throw new Error("Invalid edge location");
    }
}



