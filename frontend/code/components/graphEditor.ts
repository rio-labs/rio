import { ComponentId } from "../dataModels";
import { ComponentBase, ComponentState } from "./componentBase";
import { pixelsPerRem } from "../app";
import { componentsByElement, componentsById } from "../componentManagement";
import { NodeInputComponent } from "./nodeInput";
import { NodeOutputComponent } from "./nodeOutput";

export type GraphEditorState = ComponentState & {
    _type_: "GraphEditor-builtin";
    children?: ComponentId[];
};

type NodeState = {
    id: ComponentId;
    title: string;
    left: number;
    top: number;
};

type ConnectionState = {
    fromNode: ComponentId;
    fromPort: ComponentId;
    toNode: ComponentId;
    toPort: ComponentId;
};

type AugmentedNodeState = NodeState & {
    element: HTMLElement;
};

type AugmentedConnectionState = ConnectionState & {
    element: SVGPathElement;
};

/// A connection that is only connected to a single port, with the other end
/// currently being dragged by the user.
type LatentConnection = {
    fixedNodeId: ComponentId;
    fixedPortId: ComponentId;
    element: SVGPathElement;
};

class GraphStore {
    /// Nodes are identified by their component ID. This maps component IDs to
    /// the stored information about the node.
    private idsToNodes: Map<number, AugmentedNodeState>;

    /// This maps node IDs to connections that are connected to them.
    private nodeIdsToConnections: Map<number, AugmentedConnectionState[]>;

    constructor() {
        this.idsToNodes = new Map();
        this.nodeIdsToConnections = new Map();
    }

    /// Add a node to the store. The node must not already exist in the store.
    addNode(node: AugmentedNodeState): void {
        console.assert(
            !this.idsToNodes.has(node.id),
            `Cannot add node to GraphStore because of duplicate ID ${node.id}`
        );
        this.idsToNodes.set(node.id, node);
    }

    /// Returns an array of all nodes in the store.
    allNodes(): AugmentedNodeState[] {
        return Array.from(this.idsToNodes.values());
    }

    /// Get a node by its ID. Throws an error if the node does not exist.
    getNodeById(nodeId: number): AugmentedNodeState {
        let node = this.idsToNodes.get(nodeId);

        if (node === undefined) {
            throw new Error(`NodeEditor has no node with id ${nodeId}`);
        }

        return node;
    }

    /// Add a connection to the store. The connection must not already exist in
    /// the store.
    addConnection(conn: AugmentedConnectionState): void {
        // Sanity checks
        console.assert(
            this.idsToNodes.has(conn.fromNode),
            `Cannot add connection to GraphStore because source node ${conn.fromNode} does not exist`
        );
        console.assert(
            this.idsToNodes.has(conn.toNode),
            `Cannot add connection to GraphStore because destination node ${conn.toNode} does not exist`
        );

        // Source node
        let fromConnections = this.nodeIdsToConnections.get(conn.fromNode);

        if (fromConnections === undefined) {
            fromConnections = [];
            this.nodeIdsToConnections.set(conn.fromNode, fromConnections);
        }

        fromConnections.push(conn);

        // Destination node
        let toConnections = this.nodeIdsToConnections.get(conn.toNode);

        if (toConnections === undefined) {
            toConnections = [];
            this.nodeIdsToConnections.set(conn.toNode, toConnections);
        }

        toConnections.push(conn);
    }

    getConnectionsForNode(nodeId: number): AugmentedConnectionState[] {
        let connections = this.nodeIdsToConnections.get(nodeId);

        if (connections === undefined) {
            return [];
        }

        return connections;
    }
}

function devel_getComponentByKey(key: string): ComponentBase {
    // Temporary function to get a component by its key
    for (let component of Object.values(componentsById)) {
        if (component === undefined) {
            continue;
        }

        // @ts-ignore
        if (component.state._key_ === key) {
            return component;
        }
    }

    throw new Error(`Could not find component with key ${key}`);
}

/// Given a port component, return the node component that the port is part of.
function getNodeForPort(
    port: NodeInputComponent | NodeOutputComponent
): ComponentBase {
    let nodeElement = port.element.closest(
        ".rio-graph-editor-node > div > .rio-component"
    ) as HTMLElement;

    let nodeComponent = componentsByElement.get(nodeElement) as ComponentBase;

    return nodeComponent;
}

export class GraphEditorComponent extends ComponentBase {
    declare state: Required<GraphEditorState>;

    private htmlChild: HTMLElement;
    private svgChild: SVGSVGElement;

    private selectionChild: HTMLElement;

    private graphStore: GraphStore = new GraphStore();

    // When clicking & dragging a port, a latent connection is created. This
    // connection is already connected at one end (either start or end), but the
    // change has not yet been committed to the graph store.
    private latentConnection: LatentConnection | null = null;

    createElement(): HTMLElement {
        // Create the HTML
        let element = document.createElement("div");
        element.classList.add("rio-graph-editor");

        this.svgChild = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "svg"
        );
        element.appendChild(this.svgChild);

        this.htmlChild = document.createElement("div");
        element.appendChild(this.htmlChild);

        this.selectionChild = document.createElement("div");
        this.selectionChild.classList.add("rio-graph-editor-selection");
        this.htmlChild.appendChild(this.selectionChild);

        // Random gradient for testing
        const gradient = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "linearGradient"
        );
        gradient.setAttribute("id", "connectionGradient");
        gradient.setAttribute("x1", "0%");
        gradient.setAttribute("y1", "0%");
        gradient.setAttribute("x2", "100%");
        gradient.setAttribute("y2", "100%");

        const stop1 = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "stop"
        );
        stop1.setAttribute("offset", "0%");
        stop1.setAttribute("stop-color", "red");
        gradient.appendChild(stop1);

        const stop2 = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "stop"
        );
        stop2.setAttribute("offset", "100%");
        stop2.setAttribute("stop-color", "blue");
        gradient.appendChild(stop2);

        const defs = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "defs"
        );
        defs.appendChild(gradient);
        this.svgChild.appendChild(defs);

        // Detect clicks on ports. Just log them for now.
        //
        // This could of course be handled by the ports themselves, but then
        // they'd somehow have to pipe that event to the editor. Instead, just
        // detect the event here, and decline it if it's not on a port.
        this.addDragHandler({
            element: element,
            onStart: this._onDragPortStart.bind(this),
            onMove: this._onDragPortMove.bind(this),
            onEnd: this._onDragPortEnd.bind(this),
            capturing: true,
        });

        return element;
    }

    updateElement(
        deltaState: GraphEditorState,
        latentComponents: Set<ComponentBase>
    ): void {
        // Spawn some children for testing
        if (deltaState.children !== undefined) {
            // Spawn all nodes
            for (let ii = 0; ii < deltaState.children.length; ii++) {
                let childId = deltaState.children[ii];

                let rawNode: NodeState = {
                    id: childId,
                    title: `Node ${ii}`,
                    left: 10 + ii * 10,
                    top: 10 + ii * 10,
                };
                let augmentedNode = this._makeNode(latentComponents, rawNode);
                this.graphStore.addNode(augmentedNode);
            }

            // Connect some of them
            requestAnimationFrame(() => {
                let fromPortComponent = devel_getComponentByKey("out_1");
                let toPortComponent = devel_getComponentByKey("in_1");

                let augmentedConn: AugmentedConnectionState = {
                    // @ts-ignore
                    fromNode: deltaState.children[1],
                    fromPort: fromPortComponent.id,
                    // @ts-ignore
                    toNode: deltaState.children[2],
                    toPort: toPortComponent.id,
                    element: this._makeConnectionElement(),
                };
                this.graphStore.addConnection(augmentedConn);
                this._updateConnectionFromObject(augmentedConn);
            });
        }
    }

    _onDragPortStart(event: PointerEvent): boolean {
        // Only care about left clicks
        if (event.button !== 0) {
            return false;
        }

        // Find the port that was clicked
        let targetElement = event.target as HTMLElement;
        if (!targetElement.classList.contains("rio-graph-editor-port-circle")) {
            return false;
        }

        let portElement = targetElement.parentElement as HTMLElement;
        console.assert(
            portElement.classList.contains("rio-graph-editor-port"),
            "Port element does not have the expected class"
        );

        let portComponent = componentsByElement.get(portElement) as
            | NodeInputComponent
            | NodeOutputComponent;
        console.assert(
            portComponent !== undefined,
            "Port element does not have a corresponding component"
        );

        // Create a latent connection
        this.latentConnection = {
            fixedNodeId: getNodeForPort(portComponent).id,
            fixedPortId: portComponent.id,
            element: this._makeConnectionElement(),
        };

        return true;
    }

    _onDragPortMove(event: PointerEvent): void {
        // Make sure there is actually a latent connection. This may not always
        // be guaranteed if there are multiple pointer devices.
        if (this.latentConnection === null) {
            return;
        }

        // Update the latent connection
        const fixedPortComponent = componentsById[
            this.latentConnection.fixedPortId
        ] as NodeInputComponent | NodeOutputComponent | undefined;

        // The element could've been deleted in the meantime
        if (fixedPortComponent === undefined) {
            return;
        }

        let [x1, y1] = this._getPortPosition(fixedPortComponent);
        let [x2, y2] = [event.clientX, event.clientY];

        // If dragging from an input port, flip the coordinates
        if (fixedPortComponent instanceof NodeInputComponent) {
            [x1, y1, x2, y2] = [x2, y2, x1, y1];
        }

        // Update the SVG path
        this._updateConnectionFromCoordinates(
            this.latentConnection.element,
            x1,
            y1,
            x2,
            y2
        );
    }

    _onDragPortEnd(event: PointerEvent): void {
        // Once again, make sure there is actually a latent connection.
        if (this.latentConnection === null) {
            return;
        }

        // Drop the latent connection
        let latentConnection = this.latentConnection;
        this.latentConnection.element.remove();
        this.latentConnection = null;

        // Was the pointer released on a port?
        let dropElement = event.target as HTMLElement;

        if (!dropElement.classList.contains("rio-graph-editor-port-circle")) {
            return;
        }

        let dropPortComponent = componentsByElement.get(
            dropElement.parentElement as HTMLElement
        );

        // Get the fixed port
        let fixedPortComponent = componentsById[
            latentConnection.fixedPortId
        ] as NodeInputComponent | NodeOutputComponent;

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
        let augmentedConn: AugmentedConnectionState = {
            fromNode: getNodeForPort(fromPortComponent).id,
            fromPort: fromPortComponent.id,
            toNode: getNodeForPort(toPortComponent).id,
            toPort: toPortComponent.id,
            element: this._makeConnectionElement(),
        };
        this.graphStore.addConnection(augmentedConn);
        this._updateConnectionFromObject(augmentedConn);
    }

    _onDragNodeStart(
        nodeState: NodeState,
        nodeElement: HTMLElement,
        event: PointerEvent
    ): boolean {
        // Only care about left clicks
        if (event.button !== 0) {
            return false;
        }

        // Make sure this node is on top
        nodeElement.style.zIndex = "1";

        // Accept the drag
        return true;
    }

    _onDragNodeMove(
        nodeState: NodeState,
        nodeElement: HTMLElement,
        event: PointerEvent
    ): void {
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

    _onDragNodeEnd(
        nodeState: NodeState,
        nodeElement: HTMLElement,
        event: PointerEvent
    ): void {
        // The node no longer needs to be on top
        nodeElement.style.removeProperty("z-index");
    }

    _makeNode(
        latentComponents: Set<ComponentBase>,
        nodeState: NodeState
    ): AugmentedNodeState {
        // Build the node HTML
        const nodeElement = document.createElement("div");
        nodeElement.dataset.nodeId = nodeState.id.toString();
        nodeElement.classList.add(
            "rio-graph-editor-node",
            "rio-switcheroo-neutral"
        );
        nodeElement.style.left = `${nodeState.left}rem`;
        nodeElement.style.top = `${nodeState.top}rem`;
        this.htmlChild.appendChild(nodeElement);

        // Header
        const header = document.createElement("div");
        header.classList.add("rio-graph-editor-node-header");
        header.innerText = nodeState.title;
        nodeElement.appendChild(header);

        // Body
        const nodeBody = document.createElement("div");
        nodeBody.classList.add("rio-graph-editor-node-body");
        nodeElement.appendChild(nodeBody);

        // Content
        this.replaceOnlyChild(latentComponents, nodeState.id, nodeBody);

        // Allow dragging the node
        // @ts-ignore
        this.addDragHandler({
            element: header,
            onStart: (event: PointerEvent) =>
                this._onDragNodeStart(nodeState, nodeElement, event),
            onMove: (event: PointerEvent) =>
                this._onDragNodeMove(nodeState, nodeElement, event),
            onEnd: (event: PointerEvent) =>
                this._onDragNodeEnd(nodeState, nodeElement, event),
        });

        // Build the augmented node state
        let augmentedNode = { ...nodeState } as AugmentedNodeState;
        augmentedNode.element = nodeElement;

        return augmentedNode;
    }

    /// Creates a SVG path element representing a connection and adds it to the
    /// SVG child. Does not position the connection in any way.
    _makeConnectionElement(): SVGPathElement {
        const svgPath = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "path"
        ) as SVGPathElement;

        svgPath.setAttribute("stroke", "var(--rio-local-text-color)");
        // svgPath.setAttribute("stroke", "url(#connectionGradient)");
        svgPath.setAttribute("stroke-opacity", "0.5");
        svgPath.setAttribute("stroke-width", "0.2rem");
        svgPath.setAttribute("fill", "none");
        this.svgChild.appendChild(svgPath);

        return svgPath;
    }

    /// Given a port component, return the coordinates of the port's socket.
    _getPortPosition(
        portComponent: NodeInputComponent | NodeOutputComponent
    ): [number, number] {
        // Find the circle's HTML element
        let circleElement = portComponent.element.querySelector(
            ".rio-graph-editor-port-circle"
        ) as HTMLElement;

        // Get the circle's bounding box
        let circleBox = circleElement.getBoundingClientRect();

        // Return the center of the circle
        return [
            circleBox.left + circleBox.width * 0.5,
            circleBox.top + circleBox.height * 0.5,
        ];
    }

    _updateConnectionFromObject(
        connectionState: AugmentedConnectionState
    ): void {
        // From Port
        let fromPortComponent = componentsById[
            connectionState.fromPort
        ] as NodeOutputComponent;

        const [x1, y1] = this._getPortPosition(fromPortComponent);

        // To Port
        let toPortComponent = componentsById[
            connectionState.toPort
        ] as NodeInputComponent;

        const [x4, y4] = this._getPortPosition(toPortComponent);

        // Update the SVG path
        this._updateConnectionFromCoordinates(
            connectionState.element,
            x1,
            y1,
            x4,
            y4
        );
    }

    _updateConnectionFromCoordinates(
        connectionElement: SVGPathElement,
        x1: number,
        y1: number,
        x4: number,
        y4: number
    ): void {
        // Control the curve's bend
        let signedDistance = Math.abs(x4 - x1);

        let velocity = Math.pow(signedDistance * 10, 0.6);
        velocity = Math.max(velocity, 3 * pixelsPerRem);

        // Calculate the intermediate points
        const x2 = x1 + velocity;
        const y2 = y1;

        const x3 = x4 - velocity;
        const y3 = y4;

        // Update the SVG path
        connectionElement.setAttribute(
            "d",
            `M${x1} ${y1} C ${x2} ${y2}, ${x3} ${y3}, ${x4} ${y4}`
        );
    }
}
