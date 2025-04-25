import {
    componentsById,
    ComponentStatesUpdateContext,
} from "../componentManagement";
import { ComponentId } from "../dataModels";
import { range, zip } from "../utils";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";

type GridChildPosition = {
    row: number;
    column: number;
    width: number;
    height: number;
};

export type GridState = ComponentState & {
    _type_: "Grid-builtin";
    _children: ComponentId[];
    _child_positions: GridChildPosition[];
    row_spacing: number;
    column_spacing: number;
};

export class GridComponent extends ComponentBase<GridState> {
    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-grid");
        return element;
    }

    updateElement(
        deltaState: DeltaState<GridState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        if (deltaState._children !== undefined) {
            let childPositions =
                deltaState._child_positions ?? this.state._child_positions;

            this.replaceChildren(
                context,
                deltaState._children,
                this.element,
                true
            );

            for (let [childWrapper, childPos] of zip(
                this.element.children,
                childPositions
            )) {
                // Note: `rio.Grid` starts counting at row/column 0, but CSS
                // starts counting at 1
                let style = (childWrapper as HTMLElement).style;
                style.gridColumn = `${childPos.column + 1} / ${
                    childPos.column + 1 + childPos.width
                }`;
                style.gridRow = `${childPos.row + 1} / ${
                    childPos.row + 1 + childPos.height
                }`;
            }

            this.updateTrackSizes(deltaState._children, childPositions);
        }

        if (deltaState.row_spacing !== undefined) {
            this.element.style.rowGap = `${deltaState.row_spacing}rem`;
        }

        if (deltaState.column_spacing !== undefined) {
            this.element.style.columnGap = `${deltaState.column_spacing}rem`;
        }
    }

    onChildGrowChanged(): void {
        this.updateTrackSizes(
            this.state._children,
            this.state._child_positions
        );
    }

    updateTrackSizes(
        childIds: ComponentId[],
        childPositions: GridChildPosition[]
    ): void {
        let childrenWithPositions: [ComponentBase, GridChildPosition][] =
            childIds.map((childId: ComponentId, index: number) => [
                componentsById[childId]!,
                childPositions[index],
            ]);

        // Sort the children by the number of rows they take up
        let childrenByNumberOfRows = Array.from(childrenWithPositions);
        childrenByNumberOfRows.sort((a, b) => a[1].height - b[1].height);

        let nRows = 0;
        let growingRows = new Set();

        for (let [childComponent, childPosition] of childrenByNumberOfRows) {
            // Keep track of how how many rows this grid has
            nRows = Math.max(nRows, childPosition.row + childPosition.height);

            let allRows = range(
                childPosition.row,
                childPosition.row + childPosition.height
            );

            // Determine which rows need to grow
            if (!childComponent.state._grow_[1]) {
                continue;
            }

            // Does any of the rows already grow?
            let alreadyGrowing = allRows.some((row) => growingRows.has(row));

            // If not, mark them all as growing
            if (!alreadyGrowing) {
                for (let row of allRows) {
                    growingRows.add(row);
                }
            }
        }

        // Sort the children by the number of columns they take up
        let childrenByNumberOfColumns = Array.from(childrenWithPositions);
        childrenByNumberOfColumns.sort((a, b) => a[1].width - b[1].width);

        let nColumns = 0;
        let growingColumns = new Set();

        for (let [childComponent, childPosition] of childrenByNumberOfColumns) {
            // Keep track of how how many columns this grid has
            nColumns = Math.max(
                nColumns,
                childPosition.column + childPosition.width
            );

            let allColumns = range(
                childPosition.column,
                childPosition.column + childPosition.width
            );

            // Determine which columns need to grow
            if (!childComponent.state._grow_[0]) {
                continue;
            }

            // Does any of the rows already grow?
            let alreadyGrowing = allColumns.some((column) =>
                growingColumns.has(column)
            );

            // If not, mark them all as growing
            if (!alreadyGrowing) {
                for (let column of allColumns) {
                    growingColumns.add(column);
                }
            }
        }

        const GROW = "auto";
        const NO_GROW = "min-content";

        let columnWidths: string[] = [];
        if (growingColumns.size === 0) {
            // If nobody wants to grow, all of them do
            for (let i = 0; i < nColumns; i++) {
                columnWidths.push(GROW);
            }
        } else {
            for (let i = 0; i < nColumns; i++) {
                columnWidths.push(growingColumns.has(i) ? GROW : NO_GROW);
            }
        }

        let rowHeights: string[] = [];
        if (growingRows.size === 0) {
            // If nobody wants to grow, all of them do
            for (let i = 0; i < nRows; i++) {
                rowHeights.push(GROW);
            }
        } else {
            for (let i = 0; i < nRows; i++) {
                rowHeights.push(growingRows.has(i) ? GROW : NO_GROW);
            }
        }

        this.element.style.gridTemplateColumns = columnWidths.join(" ");
        this.element.style.gridTemplateRows = rowHeights.join(" ");
    }
}
