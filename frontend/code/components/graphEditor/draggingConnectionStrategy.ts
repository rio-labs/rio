import { componentsByElement, componentsById } from "../../componentManagement";
import { ComponentId } from "../../dataModels";
import { GraphEditorComponent } from "./graphEditor";
import { NodeInputComponent } from "../nodeInput";
import { NodeOutputComponent } from "../nodeOutput";
import {
    getNodeFromPort,
    getPortFromCircle,
    getPortViewportPosition,
    makeConnectionElement,
    updateConnectionFromCoordinates,
    updateConnectionFromObject,
} from "./utils";
import { AugmentedConnectionState } from "./graphStore";

/// The user is currently dragging a connection from a port. This means the
/// connection is already connected to one port, with the other end dangling at
/// the pointer.
export class DraggingConnectionStrategy {
    fixedNodeId: ComponentId;
    fixedPortId: ComponentId;
    element: SVGPathElement;

    constructor(
        fixedNodeId: ComponentId,
        fixedPortId: ComponentId,
        element: SVGPathElement
    ) {
        this.fixedNodeId = fixedNodeId;
        this.fixedPortId = fixedPortId;
        this.element = element;
    }

    onDragMove(ge: GraphEditorComponent, event: PointerEvent): void {
        // Update the latent connection
        const fixedPortComponent = componentsById[this.fixedPortId] as
            | NodeInputComponent
            | NodeOutputComponent
            | undefined;

        // The element could've been deleted in the meantime
        if (fixedPortComponent === undefined) {
            return;
        }

        let [x1, y1] = getPortViewportPosition(fixedPortComponent);
        let [x2, y2] = [event.clientX, event.clientY];

        // Convert the coordinates to the editor's coordinate system
        const editorRect = ge.element.getBoundingClientRect();

        x1 = x1 - editorRect.left;
        y1 = y1 - editorRect.top;
        x2 = x2 - editorRect.left;
        y2 = y2 - editorRect.top;

        // If dragging from an input port, flip the coordinates
        if (fixedPortComponent instanceof NodeInputComponent) {
            [x1, y1, x2, y2] = [x2, y2, x1, y1];
        }

        // Update the SVG path
        updateConnectionFromCoordinates(this.element, x1, y1, x2, y2);
    }

    onDragEnd(ge: GraphEditorComponent, event: PointerEvent): void {
        // Remove the SVG path
        this.element.remove();

        // Was the pointer released on a port?
        let dropElement = event.target as HTMLElement;

        if (!dropElement.classList.contains("rio-graph-editor-port-circle")) {
            return;
        }

        let dropPortComponent = getPortFromCircle(dropElement);

        // Get the fixed port
        let fixedPortComponent = componentsById[this.fixedPortId] as
            | NodeInputComponent
            | NodeOutputComponent
            | undefined;

        // The element could've been deleted in the meantime
        if (fixedPortComponent === undefined) {
            return;
        }

        // Each connection must connect exactly one input and one output
        let fromPortComponent: NodeOutputComponent;
        let toPortComponent: NodeInputComponent;

        if (fixedPortComponent instanceof NodeOutputComponent) {
            if (dropPortComponent instanceof NodeOutputComponent) {
                return;
            }

            fromPortComponent = fixedPortComponent;
            toPortComponent = dropPortComponent as NodeInputComponent;
        } else {
            if (dropPortComponent instanceof NodeInputComponent) {
                return;
            }

            fromPortComponent = dropPortComponent as NodeOutputComponent;
            toPortComponent = fixedPortComponent;
        }

        // Prepare all data needed to make the connection
        const fromNodeComponent = getNodeFromPort(fromPortComponent);
        const toNodeComponent = getNodeFromPort(toPortComponent);

        // Input nodes can only have one connection at a time. If the target
        // port already has a connection, stop here.
        let existingConnections = ge.graphStore.getConnectionsForPort(
            toNodeComponent.id,
            toPortComponent.id
        );

        if (existingConnections.length > 0) {
            return;
        }

        // Create a real connection between the two ports
        let connectionElement = makeConnectionElement();
        ge.svgChild.appendChild(connectionElement);

        let augmentedConn: AugmentedConnectionState = {
            fromNode: fromNodeComponent.id,
            fromPort: fromPortComponent.id,
            toNode: toNodeComponent.id,
            toPort: toPortComponent.id,
            element: connectionElement,
        };

        ge.graphStore.addConnection(augmentedConn);
        updateConnectionFromObject(ge, augmentedConn);
    }
}
