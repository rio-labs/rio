import { GraphEditorComponent } from "./graphEditor";
import { getPortViewportPosition, linesIntersect } from "./utils";
import { componentsById } from "../../componentManagement";
import { NodeOutputComponent } from "../nodeOutput";
import { NodeInputComponent } from "../nodeInput";
import { AugmentedConnectionState } from "./graphStore";

/// The user is dragging a line. Any nodes intersected by the line will be cut
export class CuttingConnectionStrategy {
    // These are relative to the editor, because the editor can move while the
    // strategy is active.
    startPointXInEditor: number;
    startPointYInEditor: number;

    lineElement: SVGPathElement;

    constructor(
        startPointX: number,
        startPointY: number,
        lineElement: SVGPathElement
    ) {
        this.startPointXInEditor = startPointX;
        this.startPointYInEditor = startPointY;
        this.lineElement = lineElement;
    }

    onDragMove(ge: GraphEditorComponent, event: PointerEvent): void {
        // Update the connection's points
        const editorRect = ge.element.getBoundingClientRect();

        const x1 = this.startPointXInEditor;
        const y1 = this.startPointYInEditor;

        const x2 = event.clientX - editorRect.left;
        const y2 = event.clientY - editorRect.top;

        this.lineElement.setAttributeNS(
            null,
            "d",
            `M ${x1} ${y1} L ${x2} ${y2}`
        );
    }

    onDragEnd(ge: GraphEditorComponent, event: PointerEvent): void {
        // Remove the SVG line
        this.lineElement.remove();

        // Prepare the line's coordinates, in viewport space
        const editorRect = ge.element.getBoundingClientRect();

        const cutX1 = this.startPointXInEditor + editorRect.left;
        const cutY1 = this.startPointYInEditor + editorRect.top;

        const cutX2 = event.clientX;
        const cutY2 = event.clientY;

        // Find any connections that intersect the line
        const connectionsToRemove: AugmentedConnectionState[] = [];

        for (const connection of ge.graphStore.getAllConnections()) {
            // Prepare the port positions
            let fromPortComponent = componentsById[
                connection.fromPort
            ] as NodeOutputComponent;

            let toPortComponent = componentsById[
                connection.toPort
            ] as NodeInputComponent;

            const [fromX1, fromY1] = getPortViewportPosition(fromPortComponent);
            const [toX2, toY2] = getPortViewportPosition(toPortComponent);

            // Intersecting a bezier curve is hard. Approximate it with a
            // straight line for now.
            const doesIntersect = linesIntersect(
                cutX1,
                cutY1,
                cutX2,
                cutY2,
                fromX1,
                fromY1,
                toX2,
                toY2
            );

            // Debug display
            // let lineElement = document.createElementNS(
            //     "http://www.w3.org/2000/svg",
            //     "path"
            // );
            // lineElement.setAttribute("stroke", doesIntersect ? "green" : "red");
            // lineElement.setAttribute("stroke-width", "0.15rem");
            // lineElement.setAttribute("fill", "none");
            // lineElement.setAttribute(
            //     "d",
            //     `M ${fromX1 - editorRect.left} ${fromY1 - editorRect.top} L ${
            //         toX2 - editorRect.left
            //     } ${toY2 - editorRect.top}`
            // );
            // ge.svgChild.appendChild(lineElement);

            // Remember the connection if it intersects
            if (doesIntersect) {
                connectionsToRemove.push(connection);
            }
        }

        // Remove the connections
        for (const conn of connectionsToRemove) {
            ge.graphStore.removeConnection(conn);
            conn.element.remove();
        }
    }
}
