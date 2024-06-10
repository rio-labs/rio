import { componentsById } from '../componentManagement';
import { ComponentId } from '../dataModels';
import { range, zip } from '../utils';
import { ComponentBase, ComponentState } from './componentBase';

type GridChildPosition = {
    row: number;
    column: number;
    width: number;
    height: number;
};

export type GridState = ComponentState & {
    _type_: 'Grid-builtin';
    _children?: ComponentId[];
    _child_positions?: GridChildPosition[];
    row_spacing?: number;
    column_spacing?: number;
};

export class GridComponent extends ComponentBase {
    state: Required<GridState>;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-grid');
        return element;
    }

    updateElement(
        deltaState: GridState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        let element = this.element;

        if (deltaState._children !== undefined) {
            this.replaceChildren(
                latentComponents,
                deltaState._children,
                this.element,
                true
            );

            for (let [childWrapper, childPos] of zip(
                this.element.children,
                deltaState._child_positions!
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

            this.updateTrackSizes(
                deltaState._children,
                deltaState._child_positions!
            );
        }

        if (deltaState.row_spacing !== undefined) {
            element.style.rowGap = `${deltaState.row_spacing}rem`;
        }

        if (deltaState.column_spacing !== undefined) {
            element.style.columnGap = `${deltaState.column_spacing}rem`;
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
        let maxRow = 0;
        let maxCol = 0;
        let growingColumns = new Map<number, boolean>();
        let growingRows = new Map<number, boolean>();
        let hasGrowingColumns = false;
        let hasGrowingRows = false;

        for (let [i, childPos] of childPositions.entries()) {
            let child = componentsById[childIds[i]]!;

            maxCol = Math.max(maxCol, childPos.column + childPos.width);
            maxRow = Math.max(maxRow, childPos.row + childPos.height);

            if (child.state._grow_[0]) {
                for (
                    let column = childPos.column + childPos.width - 1;
                    column >= childPos.column;
                    column--
                ) {
                    hasGrowingColumns = true;
                    growingColumns.set(column, true);
                }
            }

            if (child.state._grow_[1]) {
                for (
                    let row = childPos.row + childPos.height - 1;
                    row >= childPos.row;
                    row--
                ) {
                    hasGrowingRows = true;
                    growingRows.set(row, true);
                }
            }
        }

        const GROW = 'minmax(min-content, 1fr)';
        const NO_GROW = 'min-content';

        let columnWidths: string[] = [];
        if (hasGrowingColumns) {
            for (let i = 0; i < maxCol; i++) {
                columnWidths.push(growingColumns.get(i) ? GROW : NO_GROW);
            }
        } else {
            // If nobody wants to grow, all of them do
            for (let i = 0; i < maxCol; i++) {
                columnWidths.push(GROW);
            }
        }

        let rowHeights: string[] = [];
        if (hasGrowingRows) {
            for (let i = 0; i < maxRow; i++) {
                rowHeights.push(growingRows.get(i) ? GROW : NO_GROW);
            }
        } else {
            // If nobody wants to grow, all of them do
            for (let i = 0; i < maxRow; i++) {
                rowHeights.push(GROW);
            }
        }

        this.element.style.gridTemplateColumns = columnWidths.join(' ');
        this.element.style.gridTemplateRows = rowHeights.join(' ');
    }
}
