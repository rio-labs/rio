import { GraphEditorComponent } from "./graphEditor";

/// The user is selecting nodes by dragging a rectangle
export class DraggingSelectionStrategy {
    // These are relative to the editor, because the editor can move while the
    // strategy is active.
    startPointXInEditor: number;
    startPointYInEditor: number;

    constructor(startPointX: number, startPointY: number) {
        this.startPointXInEditor = startPointX;
        this.startPointYInEditor = startPointY;
    }

    /// Returns the [left, top, width, height] of the selection rectangle,
    /// taking care that width and height are not negative.
    ///
    /// All coordinates are relative to the editor.
    getSelectedRectangleInEditor(
        ge: GraphEditorComponent,
        event: PointerEvent
    ): [number, number, number, number] {
        let editorRect = ge.element.getBoundingClientRect();

        let rectLeft = this.startPointXInEditor;
        let rectTop = this.startPointYInEditor;
        let rectWidth =
            event.clientX - editorRect.left - this.startPointXInEditor;
        let rectHeight =
            event.clientY - editorRect.top - this.startPointYInEditor;

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

    updateSelectionRectangle(
        ge: GraphEditorComponent,
        event: PointerEvent
    ): void {
        // Get the new selection rectangle
        let [rectLeft, rectTop, rectWidth, rectHeight] =
            this.getSelectedRectangleInEditor(ge, event);

        // Apply the new values
        ge.selectionRect.style.left = `${rectLeft}px`;
        ge.selectionRect.style.top = `${rectTop}px`;
        ge.selectionRect.style.width = `${rectWidth}px`;
        ge.selectionRect.style.height = `${rectHeight}px`;
    }

    onDragMove(ge: GraphEditorComponent, event: PointerEvent): void {
        // Update the selection rectangle
        this.updateSelectionRectangle(ge, event);
    }

    onDragEnd(ge: GraphEditorComponent, event: PointerEvent): void {
        // Hide the selection rectangle
        ge.selectionRect.style.opacity = "0";

        // Get the new selection rectangle
        let editorRect = ge.element.getBoundingClientRect();

        let [rectLeft, rectTop, rectWidth, rectHeight] =
            this.getSelectedRectangleInEditor(ge, event);

        // Get the bounds in viewport coordinates
        rectLeft = rectLeft + editorRect.left;
        rectTop = rectTop + editorRect.top;

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
