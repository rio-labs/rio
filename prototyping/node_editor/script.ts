let pixelsPerRem = 16;

type NodeGraphState = {
    children?: string[];
};

type NodeState = {
    id: number;
    title: string;
    left: number;
    top: number;
};

type ConnectionState = {
    id: number;
    fromNode: number;
    fromPort: string;
    toNode: number;
    toPort: string;
};

type AugmentedNodeState = NodeState & {
    element: HTMLElement;
};

type AugmentedConnectionState = ConnectionState & {
    element: SVGPathElement;
};

class GraphStore {
    private nodes: AugmentedNodeState[];
    private connections: AugmentedConnectionState[];

    constructor() {
        this.nodes = [];
        this.connections = [];
    }

    addNode(node: AugmentedNodeState): void {
        this.nodes.push(node);
    }

    addConnection(conn: AugmentedConnectionState): void {
        this.connections.push(conn);
    }

    allNodes(): AugmentedNodeState[] {
        return this.nodes;
    }

    getNodeById(nodeId: number): AugmentedNodeState {
        for (let node of this.nodes) {
            if (node.id === nodeId) {
                return node;
            }
        }

        throw new Error(`NodeEditor has no node with id ${nodeId}`);
    }

    allConnections(): AugmentedConnectionState[] {
        return this.connections;
    }

    getConnectionsForNode(nodeId: number): AugmentedConnectionState[] {
        let result: AugmentedConnectionState[] = [];

        for (let conn of this.connections) {
            if (conn.fromNode === nodeId || conn.toNode === nodeId) {
                result.push(conn);
            }
        }

        return result;
    }
}

class DevelComponent {
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

    // Constructor
    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-node-editor');
        element.innerHTML = `
            <svg></svg>
            <div></div>
        `;

        this.htmlChild = element.querySelector('div') as HTMLElement;
        this.svgChild = element.querySelector('svg') as SVGSVGElement;

        return element;
    }

    updateElement(deltaState: NodeGraphState): void {
        if (deltaState.children !== undefined) {
            // Spawn all nodes
            for (let ii = 0; ii < deltaState.children.length; ii++) {
                let childId = deltaState.children[ii];
                let rawNode: NodeState = {
                    id: ii,
                    title: `Node ${ii}`,
                    left: 10 + ii * 10,
                    top: 10 + ii * 10,
                };

                let nodeElement = this._makeNode(rawNode, childId);
                let augmentedNode = rawNode as AugmentedNodeState;
                augmentedNode.element = nodeElement;
                this.graphStore.addNode(augmentedNode);
            }

            // Connect them
            // requestAnimationFrame(() => {
            //     for (let ii = 0; ii < deltaState.children.length - 1; ii++) {
            //         let rawConn: ConnectionState = {
            //             id: ii,
            //             fromNode: ii,
            //             fromPort: 'Output 1',
            //             toNode: ii + 1,
            //             toPort: 'Input 1',
            //         };

            //         let augmentedConn = this._makeConnection(rawConn);
            //         this.graphStore.addConnection(augmentedConn);
            //     }
            // });
        }
    }

    _beginDragNode(
        nodeState: NodeState,
        nodeElement: HTMLElement,
        event: MouseEvent
    ): boolean {
        // Only care about left clicks
        if (event.button !== 0) {
            return false;
        }

        // Make sure this node is on top
        nodeElement.style.zIndex = '1';

        // Accept the drag
        return true;
    }

    _dragMoveNode(
        nodeState: NodeState,
        nodeElement: HTMLElement,
        event: MouseEvent
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
        event: MouseEvent
    ): void {
        // The node no longer needs to be on top
        nodeElement.style.removeProperty('z-index');
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
            'http://www.w3.org/2000/svg',
            'path'
        ) as SVGPathElement;
        this.latentConnectionPath.setAttribute(
            'stroke',
            'var(--rio-local-text-color)'
        );
        this.latentConnectionPath.setAttribute('stroke-opacity', '0.5');
        this.latentConnectionPath.setAttribute('stroke-width', '0.2rem');
        this.latentConnectionPath.setAttribute('fill', 'none');
        this.latentConnectionPath.setAttribute('stroke-dasharray', '5,5');
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

    _makeshiftReplaceOnlyChild(
        childId: string,
        parentElement: HTMLElement
    ): void {
        // TODO
        // @ts-ignore
        let child = componentsById[childId]!;
        parentElement.appendChild(child.element);

        // @ts-ignore
        child.parent = this.__rioWrapper__;

        // @ts-ignore
        this.__rioWrapper__.children.add(child);
    }

    _makeNode(nodeState: NodeState, childId: string): HTMLElement {
        // Build the node HTML
        const nodeElement = document.createElement('div');
        nodeElement.dataset.nodeId = nodeState.id.toString();
        nodeElement.classList.add(
            'rio-node-editor-node',
            'rio-switcheroo-neutral'
        );
        nodeElement.style.left = `${nodeState.left}rem`;
        nodeElement.style.top = `${nodeState.top}rem`;
        this.htmlChild.appendChild(nodeElement);

        // Header
        const header = document.createElement('div');
        header.classList.add('rio-node-editor-node-header');
        header.innerText = nodeState.title;
        nodeElement.appendChild(header);

        // Body
        const nodeBody = document.createElement('div');
        nodeBody.classList.add('rio-node-editor-node-body');
        nodeElement.appendChild(nodeBody);

        // Content
        this._makeshiftReplaceOnlyChild(childId, nodeBody);

        // Inputs
        // for (let input of nodeState.inputs) {
        //     const portElement = document.createElement('div');
        //     portElement.classList.add(
        //         'rio-node-editor-port',
        //         'rio-node-editor-input'
        //     );
        //     body.appendChild(portElement);

        //     const circleElement = document.createElement('div');
        //     portElement.appendChild(circleElement);

        //     const labelElement = document.createElement('div');
        //     labelElement.innerText = input;
        //     labelElement.classList.add('rio-node-editor-port-label');
        //     portElement.appendChild(labelElement);

        //     // Allow dragging the port
        //     // @ts-ignore
        //     this.__rioWrapper__.addDragHandler({
        //         element: portElement,
        //         onStart: (event: MouseEvent) =>
        //             this._beginDragConnection(true, circleElement, event),
        //         onMove: (event: MouseEvent) => this._dragMoveConnection(event),
        //         onEnd: (event: MouseEvent) => this._endDragConnection(event),
        //     });
        // }

        // Outputs
        // for (let output of nodeState.outputs) {
        //     // Create the port
        //     const portElement = document.createElement('div');
        //     portElement.classList.add(
        //         'rio-node-editor-port',
        //         'rio-node-editor-output'
        //     );
        //     body.appendChild(portElement);

        //     const circleElement = document.createElement('div');
        //     portElement.appendChild(circleElement);

        //     const labelElement = document.createElement('div');
        //     labelElement.innerText = output;
        //     portElement.appendChild(labelElement);

        //     // Allow dragging the port
        //     // @ts-ignore
        //     this.__rioWrapper__.addDragHandler({
        //         element: portElement,
        //         onStart: (event: MouseEvent) =>
        //             this._beginDragConnection(false, circleElement, event),
        //         onMove: (event: MouseEvent) => this._dragMoveConnection(event),
        //         onEnd: (event: MouseEvent) => this._endDragConnection(event),
        //     });
        // }

        // Allow dragging the node
        // @ts-ignore
        this.__rioWrapper__.addDragHandler({
            element: header,
            onStart: (event: MouseEvent) =>
                this._beginDragNode(nodeState, nodeElement, event),
            onMove: (event: MouseEvent) =>
                this._dragMoveNode(nodeState, nodeElement, event),
            onEnd: (event: MouseEvent) =>
                this._endDragNode(nodeState, nodeElement, event),
        });

        return nodeElement;
    }

    _makeConnection(
        connectionState: ConnectionState
    ): AugmentedConnectionState {
        // Create the SVG path. Don't worry about positioning it yet
        const svgPath = document.createElementNS(
            'http://www.w3.org/2000/svg',
            'path'
        ) as SVGPathElement;

        svgPath.setAttribute('stroke', 'var(--rio-local-text-color)');
        svgPath.setAttribute('stroke-opacity', '0.5');
        svgPath.setAttribute('stroke-width', '0.2rem');
        svgPath.setAttribute('fill', 'none');
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
        let node1 = this.graphStore.getNodeById(connectionState.fromNode);
        let node2 = this.graphStore.getNodeById(connectionState.toNode);

        let port1Element = node1.element.querySelector(
            '.rio-node-editor-output > *:first-child'
        ) as HTMLElement;

        let port2Element = node2.element.querySelector(
            '.rio-node-editor-input > *:first-child'
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
            'd',
            `M${x1} ${y1} C ${x2} ${y2}, ${x3} ${y3}, ${x4} ${y4}`
        );
    }
}
