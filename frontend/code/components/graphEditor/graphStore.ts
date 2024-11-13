import { ComponentId } from "../../dataModels";
import { ComponentBase, ComponentState } from "../componentBase";
import { componentsByElement, componentsById } from "../../componentManagement";
import { NodeInputComponent } from "../nodeInput";
import { NodeOutputComponent } from "../nodeOutput";

export type GraphEditorState = ComponentState & {
    _type_: "GraphEditor-builtin";
    children?: ComponentId[];
};

export type NodeState = {
    id: ComponentId;
    title: string;
    left: number;
    top: number;
};

export type ConnectionState = {
    fromNode: ComponentId;
    fromPort: ComponentId;
    toNode: ComponentId;
    toPort: ComponentId;
};

export type AugmentedNodeState = NodeState & {
    element: HTMLElement;
};

export type AugmentedConnectionState = ConnectionState & {
    element: SVGPathElement;
};

export class GraphStore {
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

/// Given the circle HTML element of a port, walk up the DOM to find the port
/// component that contains it.A
function getPortFromCircle(
    circleElement: HTMLElement
): NodeInputComponent | NodeOutputComponent {
    let portElement = circleElement.parentElement as HTMLElement;
    console.assert(
        portElement.classList.contains("rio-graph-editor-port"),
        "Port element does not have the expected class"
    );

    let portComponent = componentsByElement.get(portElement) as ComponentBase;
    console.assert(
        portComponent !== undefined,
        "Port element does not have a corresponding component"
    );

    console.assert(
        portComponent instanceof NodeInputComponent ||
            portComponent instanceof NodeOutputComponent,
        "Port component is not of the expected type"
    );

    // @ts-ignore
    return portComponent;
}

/// Given a port component, walk up the DOM to find the node component that
/// contains it.
function getNodeFromPort(
    port: NodeInputComponent | NodeOutputComponent
): ComponentBase {
    let nodeElement = port.element.closest(
        ".rio-graph-editor-node > div > .rio-component"
    ) as HTMLElement;

    let nodeComponent = componentsByElement.get(nodeElement) as ComponentBase;

    return nodeComponent;
}
