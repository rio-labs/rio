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

    getConnectionsForPort(
        nodeId: number,
        portId: number
    ): AugmentedConnectionState[] {
        // Get all connections for this node
        let connections = this.nodeIdsToConnections.get(nodeId);

        if (connections === undefined) {
            return [];
        }

        // Filter out connections that don't involve the port
        return connections.filter(
            (conn) => conn.fromPort === portId || conn.toPort === portId
        );
    }

    getAllConnections(): AugmentedConnectionState[] {
        let result: AugmentedConnectionState[] = [];

        for (let [nodeId, connections] of this.nodeIdsToConnections) {
            // Only add connections that originate from this node. This prevents
            // connections from being added twice.
            for (let connection of connections) {
                if (connection.fromNode === nodeId) {
                    result.push(connection);
                }
            }
        }

        return result;
    }

    removeConnection(conn: AugmentedConnectionState): void {
        // Find all lists the connection could be in
        const listsToSearch: AugmentedConnectionState[][] = [];

        const fromList = this.nodeIdsToConnections.get(conn.fromNode);
        if (fromList !== undefined) {
            listsToSearch.push(fromList);
        }

        const toList = this.nodeIdsToConnections.get(conn.toNode);
        if (toList !== undefined) {
            listsToSearch.push(toList);
        }

        // Remove it
        let foundIt = false;

        for (const list of listsToSearch) {
            for (let i = 0; i < list.length; i++) {
                const other = list[i];

                if (
                    conn.fromNode === other.fromNode &&
                    conn.fromPort === other.fromPort &&
                    conn.toNode === other.toNode &&
                    conn.toPort === other.toPort
                ) {
                    list.splice(i, 1);
                    foundIt = true;
                    break;
                }
            }
        }

        // Was the connection found?
        if (!foundIt) {
            throw new Error(
                `Could not find connection to remove from node ${conn.fromNode} to node ${conn.toNode}`
            );
        }
    }
}
