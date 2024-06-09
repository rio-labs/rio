import { componentsById } from '../componentManagement';
import { ComponentId } from '../dataModels';
import { range } from '../utils';
import { ComponentBase, ComponentState } from './componentBase';

type GridChildPosition = {
    row: number;
    column: number;
    width: number;
    height: number;
};

type GridChild = {
    id: ComponentId;
    allRows: number[];
    allColumns: number[];
} & GridChildPosition;

export type GridState = ComponentState & {
    _type_: 'Grid-builtin';
    _children?: ComponentId[];
    _child_positions?: GridChildPosition[];
    row_spacing?: number;
    column_spacing?: number;
};

export class GridComponent extends ComponentBase {
    state: Required<GridState>;

    private childrenByNumberOfColumns: GridChild[];
    private childrenByNumberOfRows: GridChild[];

    private growingRows: Set<number>;
    private growingColumns: Set<number>;

    private nRows: number;
    private nColumns: number;

    private rowNaturalHeights: number[];
    private columnNaturalWidths: number[];

    private rowAllocatedHeights: number[];
    private columnAllocatedWidths: number[];

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-grid');
        return element;
    }

    precomputeChildData(deltaState: GridState): void {
        let children = deltaState._children as ComponentId[];

        // Build the list of grid children
        for (let ii = 0; ii < children.length; ii++) {
            let child = deltaState._child_positions![ii] as GridChild;
            child.id = children[ii];
            child.allRows = range(child.row, child.row + child.height);
            child.allColumns = range(child.column, child.column + child.width);
        }

        // Sort the children by the number of rows they take up
        this.childrenByNumberOfRows = Array.from(
            deltaState._child_positions!
        ) as GridChild[];
        this.childrenByNumberOfRows.sort((a, b) => a.height - b.height);

        this.nRows = 0;
        this.growingRows = new Set();

        for (let gridChild of this.childrenByNumberOfRows) {
            let childInstance = componentsById[gridChild.id]!;

            // Keep track of how how many rows this grid has
            this.nRows = Math.max(this.nRows, gridChild.row + gridChild.height);

            // Determine which rows need to grow
            if (!childInstance.state._grow_[1]) {
                continue;
            }

            // Does any of the rows already grow?
            let alreadyGrowing = gridChild.allRows.some((row) =>
                this.growingRows.has(row)
            );

            // If not, mark them all as growing
            if (!alreadyGrowing) {
                for (let row of gridChild.allRows) {
                    this.growingRows.add(row);
                }
            }
        }

        // Sort the children by the number of columns they take up
        this.childrenByNumberOfColumns = Array.from(
            this.childrenByNumberOfRows
        );
        this.childrenByNumberOfColumns.sort((a, b) => a.width - b.width);

        this.nColumns = 0;
        this.growingColumns = new Set();

        for (let gridChild of this.childrenByNumberOfColumns) {
            let childInstance = componentsById[gridChild.id]!;

            // Keep track of how how many columns this grid has
            this.nColumns = Math.max(
                this.nColumns,
                gridChild.column + gridChild.width
            );

            // Determine which columns need to grow
            if (!childInstance.state._grow_[0]) {
                continue;
            }

            // Does any of the columns already grow?
            let alreadyGrowing = gridChild.allColumns.some((column) =>
                this.growingColumns.has(column)
            );

            // If not, mark them all as growing
            if (!alreadyGrowing) {
                for (let column of gridChild.allColumns) {
                    this.growingColumns.add(column);
                }
            }
        }
    }

    updateElement(
        deltaState: GridState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        let element = this.element;

        if (deltaState._children !== undefined) {
            this.replaceChildren(latentComponents, deltaState._children);
            this.precomputeChildData(deltaState);
        }

        if (deltaState.row_spacing !== undefined) {
            element.style.rowGap = `${deltaState.row_spacing}rem`;
        }

        if (deltaState.column_spacing !== undefined) {
            element.style.columnGap = `${deltaState.column_spacing}rem`;
        }
    }
}
