import { LayoutContext } from '../layouting';
import { ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';

export type FlowState = ComponentState & {
    _type_: 'FlowContainer-builtin';
    children?: ComponentId[];
    row_spacing?: number;
    column_spacing?: number;
    justify?: 'left' | 'center' | 'right' | 'justified' | 'grow';
};

export class FlowComponent extends ComponentBase {
    state: Required<FlowState>;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-flow-container');
        return element;
    }

    updateElement(
        deltaState: FlowState,
        latentComponents: Set<ComponentBase>
    ): void {
        // Update the children
        this.replaceChildren(latentComponents, deltaState.children);

        // Regardless of whether the children or the spacing changed, a
        // re-layout is required
        this.makeLayoutDirty();
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        this.naturalWidth = 0;

        for (let child of this.children) {
            this.naturalWidth = Math.max(
                this.naturalWidth,
                child.requestedWidth
            );
        }
    }

    private processRow(row: ComponentBase[], rowWidth: number): void {
        // Determine how to use the additional space
        let spaceToTheLeft, spaceToGrow, spaceForGap;
        let additionalWidth = this.allocatedWidth - rowWidth;

        if (this.state.justify === 'left') {
            spaceToTheLeft = 0;
            spaceToGrow = 0;
            spaceForGap = 0;
        } else if (this.state.justify === 'center') {
            spaceToTheLeft = additionalWidth * 0.5;
            spaceToGrow = 0;
            spaceForGap = 0;
        } else if (this.state.justify === 'right') {
            spaceToTheLeft = additionalWidth;
            spaceToGrow = 0;
            spaceForGap = 0;
        } else if (this.state.justify === 'justified') {
            if (row.length === 1) {
                spaceToTheLeft = additionalWidth * 0.5;
                spaceToGrow = 0;
                spaceForGap = 0;
            } else {
                spaceToTheLeft = 0;
                spaceToGrow = 0;
                spaceForGap = additionalWidth / (row.length - 1);
            }
        } else {
            // 'grow'
            spaceToTheLeft = 0;
            spaceToGrow = additionalWidth / row.length;
            spaceForGap = spaceToGrow;
        }

        // Assign the positions
        for (let ii = 0; ii < row.length; ii++) {
            let child = row[ii];

            // Assign the position
            let left =
                (child as any)._flowContainer_posX +
                spaceToTheLeft +
                ii * spaceForGap;
            child.element.style.left = `${left}rem`;

            // Assign the width
            child.allocatedWidth = child.requestedWidth + spaceToGrow;
        }
    }

    updateAllocatedWidth(ctx: LayoutContext): void {
        // Allow the code below to assume there's at least one child
        if (this.children.size === 0) {
            return;
        }

        // Divide the children into rows
        //
        // For performance and simplicity, store the row index and x positions
        // right inside the children.
        let posX = 0;
        let rowIndex = 0;
        let currentRow: ComponentBase[] = [];

        for (let child of this.children) {
            // If the child is too wide, move on to the next row
            if (posX + child.requestedWidth > this.allocatedWidth) {
                this.processRow(currentRow, posX - this.state.column_spacing);

                posX = 0;
                ++rowIndex;
                currentRow = [];
            }

            // Assign the child to the row
            (child as any)._flowContainer_rowIndex = rowIndex;
            (child as any)._flowContainer_posX = posX;
            currentRow.push(child);

            // Advance the position
            posX += child.requestedWidth + this.state.column_spacing;
        }

        // Process the final row
        this.processRow(currentRow, posX - this.state.column_spacing);
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        // Allow the code below to assume there's at least one child
        if (this.children.size === 0) {
            this.naturalHeight = 0;
            return;
        }

        // Find the tallest child for each row
        let rowHeights: number[] = [];

        for (let child of this.children) {
            let rowIndex = (child as any)._flowContainer_rowIndex;
            let childHeight = child.requestedHeight;

            if (rowHeights[rowIndex] === undefined) {
                rowHeights[rowIndex] = childHeight;
            } else {
                rowHeights[rowIndex] = Math.max(
                    rowHeights[rowIndex],
                    childHeight
                );
            }
        }

        // Determine the total height
        let rowTops: number[] = [0];

        for (let ii = 0; ii < rowHeights.length; ii++) {
            rowTops.push(rowTops[ii] + rowHeights[ii] + this.state.row_spacing);
        }

        this.naturalHeight = rowTops[rowTops.length - 1];

        // Position the children
        for (let child of this.children) {
            let rowIndex = (child as any)._flowContainer_rowIndex;
            let rowTop = rowTops[rowIndex];
            let childHeight = rowHeights[rowIndex];

            child.element.style.top = `${rowTop}rem`;
            // child.element.style.height = `${childHeight}rem`;
            child.allocatedHeight = childHeight;
        }
    }

    updateAllocatedHeight(ctx: LayoutContext): void {}
}
