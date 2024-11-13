/// A connection that is only connected to a single port, with the other end

import { componentsByElement } from "../../componentManagement";
import { ComponentId } from "../../dataModels";
import { GraphEditorComponent } from "./graphEditor";
import { NodeInputComponent } from "../nodeInput";
import { NodeOutputComponent } from "../nodeOutput";

export class DraggingNodesStrategy {
    onDragMove(this_: GraphEditorComponent, event: PointerEvent): void {
        // Update the node state
        nodeState.left += event.movementX / pixelsPerRem;
        nodeState.top += event.movementY / pixelsPerRem;

        // Move its element
        nodeElement.style.left = `${nodeState.left}rem`;
        nodeElement.style.top = `${nodeState.top}rem`;

        // Update any connections
        let connections = this.graphStore.getConnectionsForNode(nodeState.id);

        for (let conn of connections) {
            this._updateConnectionFromObject(conn);
        }
    }

    onDragEnd(this_: GraphEditorComponent, event: PointerEvent): void {
        // The node no longer needs to be on top
        nodeElement.style.removeProperty("z-index");

        return false;
    }
}
