import { GraphEditorComponent } from "./graphEditor";
import { pixelsPerRem } from "../../app";
import {
    getPortPosition,
    linesIntersect,
    updateConnectionFromObject,
} from "./utils";
import { componentsById } from "../../componentManagement";
import { NodeOutputComponent } from "../nodeOutput";
import { NodeInputComponent } from "../nodeInput";
import { AugmentedConnectionState } from "./graphStore";

/// The user is dragging a line. Any nodes intersected by the line will be cut
export class CuttingConnectionStrategy {
    startPointX: number;
    startPointY: number;
    lineElement: SVGPathElement;

    constructor(
        startPointX: number,
        startPointY: number,
        lineElement: SVGPathElement
    ) {
        this.startPointX = startPointX;
        this.startPointY = startPointY;
        this.lineElement = lineElement;
    }

    onDragMove(ge: GraphEditorComponent, event: PointerEvent): void {
        // Update the connection's points
        const x1 = this.startPointX;
        const y1 = this.startPointY;

        const x2 = event.clientX;
        const y2 = event.clientY;

        this.lineElement.setAttributeNS(
            null,
            "d",
            `M ${x1} ${y1} L ${x2} ${y2}`
        );
    }

    onDragEnd(ge: GraphEditorComponent, event: PointerEvent): void {
        // Remove the SVG line
        this.lineElement.remove();

        // Find any connections that intersect the line
        const connectionsToRemove: AugmentedConnectionState[] = [];

        const cutX1 = this.startPointX;
        const cutY1 = this.startPointY;

        const cutX2 = event.clientX;
        const cutY2 = event.clientY;

        for (const connection of ge.graphStore.getAllConnections()) {
            // Prepare the port positions
            let fromPortComponent = componentsById[
                connection.fromPort
            ] as NodeOutputComponent;

            let toPortComponent = componentsById[
                connection.toPort
            ] as NodeInputComponent;

            const [fromX1, fromY1] = getPortPosition(fromPortComponent);
            const [toX2, toY2] = getPortPosition(toPortComponent);

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
            //     `M ${fromX1} ${fromY1} L ${toX2} ${toY2}`
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
