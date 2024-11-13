import { GraphEditorComponent } from "./graphEditor";

/// The user is selecting nodes by dragging a rectangle
export class DraggingSelectionStrategy {
    startPointX: number;
    startPointY: number;

    constructor(startPointX: number, startPointY: number) {
        this.startPointX = startPointX;
        this.startPointY = startPointY;
    }

    /// Returns the [left, top, width, height] of the selection rectangle,
    /// taking care that width and height are not negative.
    getSelectedRectangle(
        event: PointerEvent
    ): [number, number, number, number] {
        let rectLeft = this.startPointX;
        let rectTop = this.startPointY;
        let rectWidth = event.clientX - this.startPointX;
        let rectHeight = event.clientY - this.startPointY;

        // Avoid negative width and height
        if (rectWidth < 0) {
            rectLeft += rectWidth;
            rectWidth = -rectWidth;
        }

        if (rectHeight < 0) {
            rectTop += rectHeight;
            rectHeight = -rectHeight;
        }

        // Done
        return [rectLeft, rectTop, rectWidth, rectHeight];
    }

    onDragMove(ge: GraphEditorComponent, event: PointerEvent): void {
        // Get the new selection rectangle
        let [rectLeft, rectTop, rectWidth, rectHeight] =
            this.getSelectedRectangle(event);

        // Apply the new values
        ge.selectionRect.style.left = `${rectLeft}px`;
        ge.selectionRect.style.top = `${rectTop}px`;
        ge.selectionRect.style.width = `${rectWidth}px`;
        ge.selectionRect.style.height = `${rectHeight}px`;
    }

    onDragEnd(ge: GraphEditorComponent, event: PointerEvent): void {
        // Hide the selection rectangle
        ge.selectionRect.style.opacity = "0";

        // Get the new selection rectangle
        let [rectLeft, rectTop, rectWidth, rectHeight] =
            this.getSelectedRectangle(event);

        let rectRight = rectLeft + rectWidth;
        let rectBottom = rectTop + rectHeight;

        // Select all nodes that fall within the selection rectangle
        for (let node of ge.graphStore.allNodes()) {
            let nodeElement = node.element;

            // Get the bounding box of the node
            let nodeBox = nodeElement.getBoundingClientRect();

            // Check if the node is within the selection rectangle
            if (
                nodeBox.left >= rectLeft &&
                nodeBox.right <= rectRight &&
                nodeBox.top >= rectTop &&
                nodeBox.bottom <= rectBottom
            ) {
                ge.selectNode(node);
            }
        }
    }
}
