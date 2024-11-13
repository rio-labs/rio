import { ComponentId } from "../dataModels";
import { ComponentBase, ComponentState } from "./componentBase";
import { pixelsPerRem } from "../app";
import { componentsById } from "../componentManagement";

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

class GraphStore {
    /// Nodes are identified by their component ID. This maps component IDs to
    /// the stored information about the node.
    private idsToNodes: Map<number, AugmentedNodeState>;

    /// This maps node IDs to connections that are connected to them.
    private idsToConnections: Map<number, AugmentedConnectionState[]>;

    constructor() {
        this.idsToNodes = new Map();
        this.idsToConnections = new Map();
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
        let fromConnections = this.idsToConnections.get(conn.fromNode);

        if (fromConnections === undefined) {
            fromConnections = [];
            this.idsToConnections.set(conn.fromNode, fromConnections);
        }

        fromConnections.push(conn);

        // Destination node
        let toConnections = this.idsToConnections.get(conn.toNode);

        if (toConnections === undefined) {
            toConnections = [];
            this.idsToConnections.set(conn.toNode, toConnections);
        }

        toConnections.push(conn);
    }

    getConnectionsForNode(nodeId: number): AugmentedConnectionState[] {
        let connections = this.idsToConnections.get(nodeId);

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

export class GraphEditorComponent extends ComponentBase {
    declare state: Required<GraphEditorState>;

    private htmlChild: HTMLElement;
    private svgChild: SVGSVGElement;

    private graphStore: GraphStore = new GraphStore();

    // When clicking & dragging a port, a latent connection is created. This
    // connection is already connected at one end (either start or end), but the
    // change has not yet been committed to the graph store.
    private latentConnectionStartElement: HTMLElement | null;
    private latentConnectionEndElement: HTMLElement | null;
    private latentConnectionPath: SVGPathElement | null;

    // This may be null even if a port is currently being dragged, if the latent
    // connection is new, rather than one that already existed on the graph.
    private latentConnection: AugmentedConnectionState | null;

    // True if `updateElement` has been called at least once
    private isInitialized: boolean = false;

    createElement(): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-graph-editor");
        element.innerHTML = `
            <svg></svg>
            <div></div>
        `;

        this.htmlChild = element.querySelector("div") as HTMLElement;
        this.svgChild = element.querySelector("svg") as SVGSVGElement;

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

                let rawConn: ConnectionState = {
                    fromNode: deltaState.children[1],
                    fromPort: fromPortComponent.id,
                    toNode: deltaState.children[2],
                    toPort: toPortComponent.id,
                };
                let augmentedConn = this._makeConnection(rawConn);
                this.graphStore.addConnection(augmentedConn);
            });
        }

        // This component is now initialized
        this.isInitialized = true;
    }

    _beginDragNode(
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

    _dragMoveNode(
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
            this._updateConnection(conn);
        }
    }

    _endDragNode(
        nodeState: NodeState,
        nodeElement: HTMLElement,
        event: PointerEvent
    ): void {
        // The node no longer needs to be on top
        nodeElement.style.removeProperty("z-index");
    }

    _beginDragConnection(
        isInput: boolean,
        portElement: HTMLElement,
        event: MouseEvent
    ): boolean {
        // Only care about left clicks
        if (event.button !== 0) {
            return false;
        }

        // Create a latent connection
        this.latentConnectionPath = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "path"
        ) as SVGPathElement;
        this.latentConnectionPath.setAttribute(
            "stroke",
            "var(--rio-local-text-color)"
        );
        this.latentConnectionPath.setAttribute("stroke-opacity", "0.5");
        this.latentConnectionPath.setAttribute("stroke-width", "0.2rem");
        this.latentConnectionPath.setAttribute("fill", "none");
        this.latentConnectionPath.setAttribute("stroke-dasharray", "5,5");
        this.svgChild.appendChild(this.latentConnectionPath);

        if (isInput) {
            this.latentConnectionStartElement = null;
            this.latentConnectionEndElement = portElement;
        } else {
            this.latentConnectionStartElement = portElement;
            this.latentConnectionEndElement = null;
        }

        // If a connection was already connected to this port, it is being
        // dragged now.
        this.latentConnection = null;
        // TODO

        // Accept the drag
        return true;
    }

    _dragMoveConnection(event: MouseEvent): void {
        // Update the latent connection
        let x1, y1, x4, y4;

        if (this.latentConnectionStartElement !== null) {
            let startPoint =
                this.latentConnectionStartElement!.getBoundingClientRect();
            x1 = startPoint.left + startPoint.width * 0.5;
            y1 = startPoint.top + startPoint.height * 0.5;

            x4 = event.clientX;
            y4 = event.clientY;
        } else {
            x1 = event.clientX;
            y1 = event.clientY;

            let endPoint =
                this.latentConnectionEndElement!.getBoundingClientRect();
            x4 = endPoint.left + endPoint.width * 0.5;
            y4 = endPoint.top + endPoint.height * 0.5;
        }

        this._updateConnectionPath(this.latentConnectionPath!, x1, y1, x4, y4);
    }

    _endDragConnection(event: MouseEvent): void {
        // Remove the latent connection
        this.latentConnectionPath!.remove();

        // Reset state
        this.latentConnectionStartElement = null;
        this.latentConnectionEndElement = null;
        this.latentConnectionPath = null;
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
                this._beginDragNode(nodeState, nodeElement, event),
            onMove: (event: PointerEvent) =>
                this._dragMoveNode(nodeState, nodeElement, event),
            onEnd: (event: PointerEvent) =>
                this._endDragNode(nodeState, nodeElement, event),
        });

        // Build the augmented node state
        let augmentedNode = { ...nodeState } as AugmentedNodeState;
        augmentedNode.element = nodeElement;

        return augmentedNode;
    }

    _makeConnection(
        connectionState: ConnectionState
    ): AugmentedConnectionState {
        // Create the SVG path. Don't worry about positioning it yet
        const svgPath = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "path"
        ) as SVGPathElement;

        svgPath.setAttribute("stroke", "var(--rio-local-text-color)");
        svgPath.setAttribute("stroke-opacity", "0.5");
        svgPath.setAttribute("stroke-width", "0.2rem");
        svgPath.setAttribute("fill", "none");
        this.svgChild.appendChild(svgPath);

        // Augment the connection state
        let augmentedConn = connectionState as AugmentedConnectionState;
        augmentedConn.element = svgPath;

        // Update the connection
        this._updateConnection(augmentedConn);

        return augmentedConn;
    }

    _updateConnection(connectionState: AugmentedConnectionState): void {
        // Get the port elements
        let fromNodeState = this.graphStore.getNodeById(
            connectionState.fromNode
        );
        let toNodeState = this.graphStore.getNodeById(connectionState.toNode);

        console.log(fromNodeState, toNodeState);

        let port1Element = fromNodeState.element.querySelector(
            ".rio-graph-editor-output > *:first-child"
        ) as HTMLElement;

        let port2Element = toNodeState.element.querySelector(
            ".rio-graph-editor-input > *:first-child"
        ) as HTMLElement;

        const box1 = port1Element.getBoundingClientRect();
        const box2 = port2Element.getBoundingClientRect();

        // Calculate the start and end points
        const x1 = box1.left + box1.width * 0.5;
        const y1 = box1.top + box1.height * 0.5;

        const x4 = box2.left + box2.width * 0.5;
        const y4 = box2.top + box2.height * 0.5;

        // Update the SVG path
        this._updateConnectionPath(connectionState.element, x1, y1, x4, y4);
    }

    _updateConnectionPath(
        connectionElement: SVGPathElement,
        x1: number,
        y1: number,
        x4: number,
        y4: number
    ): void {
        // Control the curve's bend
        let signedDistance = x4 - x1;

        let velocity = Math.sqrt(Math.abs(signedDistance * 20));
        velocity = Math.max(velocity, 2 * pixelsPerRem);

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
