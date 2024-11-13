import { componentsByElement, componentsById } from "../../componentManagement";
import { ComponentId } from "../../dataModels";
import { GraphEditorComponent } from "./graphEditor";
import { NodeInputComponent } from "../nodeInput";
import { NodeOutputComponent } from "../nodeOutput";
import {
    getNodeFromPort,
    getPortFromCircle,
    getPortPosition,
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

    onDragMove(this_: GraphEditorComponent, event: PointerEvent): void {
        // Update the latent connection
        const fixedPortComponent = componentsById[this.fixedPortId] as
            | NodeInputComponent
            | NodeOutputComponent
            | undefined;

        // The element could've been deleted in the meantime
        if (fixedPortComponent === undefined) {
            return;
        }

        let [x1, y1] = getPortPosition(fixedPortComponent);
        let [x2, y2] = [event.clientX, event.clientY];

        // If dragging from an input port, flip the coordinates
        if (fixedPortComponent instanceof NodeInputComponent) {
            [x1, y1, x2, y2] = [x2, y2, x1, y1];
        }

        // Update the SVG path
        updateConnectionFromCoordinates(this.element, x1, y1, x2, y2);
    }

    onDragEnd(this_: GraphEditorComponent, event: PointerEvent): void {
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

        // Create a real connection between the two ports
        let connectionElement = makeConnectionElement();
        this_.svgChild.appendChild(connectionElement);

        let augmentedConn: AugmentedConnectionState = {
            fromNode: getNodeFromPort(fromPortComponent).id,
            fromPort: fromPortComponent.id,
            toNode: getNodeFromPort(toPortComponent).id,
            toPort: toPortComponent.id,
            element: connectionElement,
        };

        this_.graphStore.addConnection(augmentedConn);
        updateConnectionFromObject(augmentedConn);
    }
}
