import { GraphEditorComponent } from "./graphEditor";
import { pixelsPerRem } from "../../app";
import { updateConnectionFromObject } from "./utils";
import { AugmentedNodeState } from "./graphStore";

/// The user is moving around all selected nodes
export class DraggingNodesStrategy {
    nodesToMove: AugmentedNodeState[] = [];

    constructor(nodesToMove: AugmentedNodeState[]) {
        this.nodesToMove = nodesToMove;
    }

    onDragMove(ge: GraphEditorComponent, event: PointerEvent): void {
        // Move all selected nodes
        let moveX = event.movementX / pixelsPerRem;
        let moveY = event.movementY / pixelsPerRem;

        for (let nodeState of this.nodesToMove) {
            // Update the stored position
            nodeState.left += moveX;
            nodeState.top += moveY;

            // Move the HTML element
            nodeState.element.style.left = `${nodeState.left}rem`;
            nodeState.element.style.top = `${nodeState.top}rem`;
        }

        // Update any connections
        for (let nodeState of this.nodesToMove) {
            for (let connection of ge.graphStore.getConnectionsForNode(
                nodeState.id
            )) {
                updateConnectionFromObject(ge, connection);
            }
        }
    }

    onDragEnd(ge: GraphEditorComponent, event: PointerEvent): void {
        // The nodes no longer needs to be on top
        for (let nodeState of ge.getSelectedNodes()) {
            nodeState.element.style.removeProperty("z-index");
        }
    }
}
