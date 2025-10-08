import { FrontendNode } from "@/types/node";


function sourceIsAboveTarget(sourceNode: FrontendNode, targetNode: FrontendNode) {
    return sourceNode.yPosition < targetNode.yPosition;
}

function sourceIsToTheRightOfTarget(sourceNode: FrontendNode, targetNode: FrontendNode) {
    return targetNode.xPosition + 200 < sourceNode.xPosition;
}

function sourceIsBelowTarget(sourceNode: FrontendNode, targetNode: FrontendNode) {
    return sourceNode.yPosition > targetNode.yPosition;
}

function sourceIsToTheLeftOfTarget(sourceNode: FrontendNode, targetNode: FrontendNode) {
    return sourceNode.xPosition < targetNode.xPosition - 200;
}

type Edge = {
    from: "left-source" | "right-source" | "bottom-source" | "top-source";
    to: "left-target" | "right-target" | "bottom-target" | "top-target";
}

export function computeBoxEdgeLocations(sourceNode: FrontendNode, targetNode: FrontendNode): Edge {
    if (sourceIsToTheRightOfTarget(sourceNode, targetNode)){
        return { from: "left-source", to: "right-target" };
    }
    else if (sourceIsToTheLeftOfTarget(sourceNode, targetNode)){
        return { from: "right-source", to: "left-target" };
    }
    else if (sourceIsBelowTarget(sourceNode, targetNode)){
        return { from: "top-source", to: "bottom-target" };
    }
    else if (sourceIsAboveTarget(sourceNode, targetNode)){
        return { from: "bottom-source", to: "top-target" };
    }
    else {
        throw new Error("Invalid edge location");
    }
}



