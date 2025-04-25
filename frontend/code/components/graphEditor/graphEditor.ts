import { ComponentId } from "../../dataModels";
import { ComponentBase, ComponentState, DeltaState } from "../componentBase";
import { NodeInputComponent } from "../nodeInput";
import {
    AugmentedConnectionState,
    AugmentedNodeState,
    GraphStore,
    NodeState,
} from "./graphStore";
import { DraggingConnectionStrategy } from "./draggingConnectionStrategy";
import { DraggingSelectionStrategy } from "./draggingSelectionStrategy";
import { DraggingNodesStrategy } from "./draggingNodesStrategy";
import {
    devel_getComponentByKey,
    getNodeComponentFromElement,
    getNodeFromPort,
    getPortFromCircle,
    makeConnectionElement,
    updateConnectionFromObject,
} from "./utils";
import { CuttingConnectionStrategy } from "./cuttingConnectionStrategy";
import { ComponentStatesUpdateContext } from "../../componentManagement";

export type GraphEditorState = ComponentState & {
    _type_: "GraphEditor-builtin";
    children: ComponentId[];
};

export class GraphEditorComponent extends ComponentBase<GraphEditorState> {
    private htmlChild: HTMLElement;
    public svgChild: SVGSVGElement;

    public selectionRect: HTMLElement;

    public graphStore: GraphStore = new GraphStore();

    /// All currently selected nodes, if any. This is intentionally private,
    /// because adding & removing nodes also needs to update their styles
    /// accordingly.
    private selectedNodes: Set<ComponentId> = new Set();

    /// When clicking & dragging a variety of things can happen based on the
    /// selection, mouse button, position and phase of the moon. This strategy
    /// object is used in lieu of if-else chains.
    private dragStrategy:
        | CuttingConnectionStrategy
        | DraggingConnectionStrategy
        | DraggingSelectionStrategy
        | DraggingNodesStrategy
        | null = null;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
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

        this.selectionRect = document.createElement("div");
        this.selectionRect.classList.add("rio-graph-editor-selection");
        this.selectionRect.style.opacity = "0";
        this.htmlChild.appendChild(this.selectionRect);

        // Listen for drag events. The exact nature of the drag event is
        // determined by the current drag strategy.
        this.addDragHandler({
            element: element,
            onStart: this._onDragStart.bind(this),
            onMove: this._onDragMove.bind(this),
            onEnd: this._onDragEnd.bind(this),
            capturing: true,
        });

        return element;
    }

    updateElement(
        deltaState: DeltaState<GraphEditorState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

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
                let augmentedNode = this._makeNode(context, rawNode);
                this.graphStore.addNode(augmentedNode);
            }

            // Connect some of them
            requestAnimationFrame(() => {
                let fromPortComponent = devel_getComponentByKey("out_1");
                let toPortComponent = devel_getComponentByKey("in_1");

                let connectionElement = makeConnectionElement();
                this.svgChild.appendChild(connectionElement);

                let augmentedConn: AugmentedConnectionState = {
                    // @ts-ignore
                    fromNode: deltaState.children[1],
                    fromPort: fromPortComponent.id,
                    // @ts-ignore
                    toNode: deltaState.children[2],
                    toPort: toPortComponent.id,
                    element: connectionElement,
                };
                this.graphStore.addConnection(augmentedConn);
                updateConnectionFromObject(this, augmentedConn);
            });
        }
    }

    _onDragStart(event: PointerEvent): boolean {
        // If a drag strategy is already active, ignore this event
        if (this.dragStrategy !== null) {
            return false;
        }

        // FIXME: A lot of the strategies below are checking for the left mouse
        // button. This is wrong on touch and pointer devices.
        const isLeftClick = event.button === 0;
        const isHoldingCtrl = event.ctrlKey;

        let targetElement = event.target as HTMLElement;
        console.assert(
            targetElement !== null,
            "Pointer event has no target element"
        );

        // Find an applicable strategy
        //
        // Case: Cutting connections
        if (isLeftClick && isHoldingCtrl) {
            // Add a line to the SVG. It provides feedback to the user as to
            // which connections will be cut.
            let lineElement = document.createElementNS(
                "http://www.w3.org/2000/svg",
                "path"
            );
            lineElement.setAttribute("stroke", "var(--rio-global-danger-bg)");
            lineElement.setAttribute("stroke-width", "0.15rem");
            lineElement.setAttribute("fill", "none");
            this.svgChild.appendChild(lineElement);

            // Store the strategy
            const editorRect = this.element.getBoundingClientRect();

            this.dragStrategy = new CuttingConnectionStrategy(
                event.clientX - editorRect.left,
                event.clientY - editorRect.top,
                lineElement
            );

            // Accept the drag
            return true;
        }

        // Case: Create / move connection from a port
        if (
            isLeftClick &&
            targetElement.classList.contains("rio-graph-editor-port-circle")
        ) {
            let portComponent = getPortFromCircle(targetElement);

            // If this is an input port, and it already has a connection
            // attached, drag that connection.
            let fixedNodeId: ComponentId = getNodeFromPort(portComponent).id;
            let fixedPortId: ComponentId = portComponent.id;

            if (portComponent instanceof NodeInputComponent) {
                let connections = this.graphStore.getConnectionsForPort(
                    fixedNodeId,
                    fixedPortId
                );

                console.assert(
                    connections.length <= 1,
                    `Input ports should have at most one connection, but port ${portComponent.id} has ${connections.length}`
                );

                // If a connection was found, remove it and drag that one
                if (connections.length === 1) {
                    let connection = connections[0];
                    this.graphStore.removeConnection(connection);
                    connection.element.remove();

                    fixedNodeId = connection.fromNode;
                    fixedPortId = connection.fromPort;
                }
            }

            // Add a new connection to the SVG
            let connectionElement = makeConnectionElement();
            this.svgChild.appendChild(connectionElement);

            // Store the strategy
            this.dragStrategy = new DraggingConnectionStrategy(
                fixedNodeId,
                fixedPortId,
                connectionElement
            );

            return true;
        }

        // Case: Move around the selected nodes
        if (
            isLeftClick &&
            targetElement.classList.contains("rio-graph-editor-node-header")
        ) {
            // Determine which nodes to move
            let targetedComponent = getNodeComponentFromElement(
                targetElement.parentElement!
            );
            let targetedNodeState = this.graphStore.getNodeById(
                targetedComponent.id
            );
            let nodesToMove: AugmentedNodeState[] = [];

            // If this node is selected, move the entire selection
            if (this.selectedNodes.has(targetedNodeState.id)) {
                for (const node of this.getSelectedNodes()) {
                    nodesToMove.push(node);
                }
            }
            // Otherwise make this node the sole selection
            else {
                this.deselectAllNodes();
                this.selectNode(targetedNodeState);
                nodesToMove.push(targetedNodeState);
            }

            // Make sure all selected nodes are on top
            for (let node of nodesToMove) {
                node.element.style.zIndex = "1";
            }

            // Store the strategy
            this.dragStrategy = new DraggingNodesStrategy(nodesToMove);

            // Accept the drag
            return true;
        }

        // Case: Rectangle selection
        if (isLeftClick && targetElement === this.htmlChild) {
            // Deselect any previously selected nodes
            this.deselectAllNodes();

            // Store the strategy
            let editorRect = this.element.getBoundingClientRect();
            this.dragStrategy = new DraggingSelectionStrategy(
                event.clientX - editorRect.left,
                event.clientY - editorRect.top
            );

            // Initialize the selection rectangle
            this.selectionRect.style.opacity = "1";
            this.dragStrategy.updateSelectionRectangle(this, event);

            // Accept the drag
            return true;
        }

        // No strategy found
        console.assert(
            this.dragStrategy === null,
            "A drag strategy was found, but the function hasn't returned"
        );
        return false;
    }

    _onDragMove(event: PointerEvent): void {
        // If no drag strategy is active, there's nothing to do
        if (this.dragStrategy === null) {
            return;
        }

        // Delegate to the drag strategy
        this.dragStrategy.onDragMove(this, event);
    }

    _onDragEnd(event: PointerEvent): void {
        // If no drag strategy is active, there's nothing to do
        if (this.dragStrategy === null) {
            return;
        }

        // Delegate to the drag strategy
        this.dragStrategy.onDragEnd(this, event);

        // Clear the drag strategy
        this.dragStrategy = null;
    }

    /// Creates a node element and adds it to the HTML child. Returns the node
    /// state, augmented with the HTML element.
    _makeNode(
        context: ComponentStatesUpdateContext,
        nodeState: NodeState
    ): AugmentedNodeState {
        // Build the node HTML
        const nodeElement = document.createElement("div");
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
        this.replaceOnlyChild(context, nodeState.id, nodeBody);

        // Build the augmented node state
        let augmentedNode = { ...nodeState } as AugmentedNodeState;
        augmentedNode.element = nodeElement;

        return augmentedNode;
    }

    /// Adds the given node to the set of selected nodes and updates its style
    /// appropriately.
    ///
    /// Does nothing if the node is already selected.
    public selectNode(node: AugmentedNodeState): void {
        // Add to the set of selected nodes
        this.selectedNodes.add(node.id);

        // Update the CSS
        node.element.classList.add("rio-graph-editor-selected-node");
    }

    /// Removes the given node from the set of selected nodes and updates its
    /// style appropriately.
    ///
    /// Does nothing if the node is not selected.
    public deselectNode(node: AugmentedNodeState): void {
        // Remove from the set of selected nodes
        this.selectedNodes.delete(node.id);

        // Update the CSS
        node.element.classList.remove("rio-graph-editor-selected-node");
    }

    /// Deselects all nodes.
    public deselectAllNodes(): void {
        let selectedNodes = Array.from(this.getSelectedNodes());

        for (let node of selectedNodes) {
            this.deselectNode(node);
        }
    }

    /// Returns an iterable over all selected nodes.
    public getSelectedNodes(): Iterable<AugmentedNodeState> {
        let result: AugmentedNodeState[] = [];

        for (let nodeId of this.selectedNodes) {
            let node = this.graphStore.getNodeById(nodeId);

            if (node !== undefined) {
                result.push(node);
            }
        }

        return result;
    }
}
