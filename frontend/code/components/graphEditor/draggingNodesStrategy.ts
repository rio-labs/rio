import { GraphEditorComponent } from "./graphEditor";
import { pixelsPerRem } from "../../app";
import { updateConnectionFromObject } from "./utils";

/// The user is moving around all selected nodes
export class DraggingNodesStrategy {
    onDragMove(ge: GraphEditorComponent, event: PointerEvent): void {
        // Move all selected nodes
        let moveX = event.movementX / pixelsPerRem;
        let moveY = event.movementY / pixelsPerRem;

        for (let nodeState of ge.getSelectedNodes()) {
            // Update the stored position
            nodeState.left += moveX;
            nodeState.top += moveY;

            // Move the HTML element
            nodeState.element.style.left = `${nodeState.left}rem`;
            nodeState.element.style.top = `${nodeState.top}rem`;
        }

        // Update any connections
        for (let nodeState of ge.getSelectedNodes()) {
            for (let connection of ge.graphStore.getConnectionsForNode(
                nodeState.id
            )) {
                updateConnectionFromObject(connection);
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
