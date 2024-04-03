import { getElementDimensions } from '../layoutHelpers';
import { LayoutContext } from '../layouting';
import { ComponentBase, ComponentState } from './componentBase';

type TableValue = number | string;
type DataFromBackend = { [label: string]: TableValue[] } | TableValue[][];

type TableDeltaState = ComponentState & {
    _type_: 'Table-builtin';
    data?: DataFromBackend;
    show_row_numbers?: boolean;
};

// We can receive data either as an object or as a 2d array, but we store it
// as an array of Columns
type TableState = Omit<Required<TableDeltaState>, 'data'> & { data: Column[] };

class Column {
    public name: string;
    public dataType: 'number' | 'text' | 'empty';
    public alignment: string;
    public values: TableValue[];

    constructor(name: string, values: TableValue[]) {
        this.name = name;
        this.values = values;
        this.dataType = this._determineDataType(values);
        this.alignment = this.dataType === 'number' ? 'right' : 'left';
    }

    private _determineDataType(
        values: TableValue[]
    ): 'number' | 'text' | 'empty' {
        if (values.length === 0) {
            return 'empty';
        }

        if (typeof values[0] === 'number') {
            return 'number';
        }

        return 'text';
    }
}

function dataToColumns(data: DataFromBackend): Column[] {
    let columns: Column[] = [];

    if (Array.isArray(data)) {
        let numColumns = data.length === 0 ? 0 : data[0].length;

        for (let i = 0; i < numColumns; i++) {
            let values = data.map((row) => row[i]);
            columns.push(new Column('', values));
        }
    } else {
        for (let [name, values] of Object.entries(data)) {
            columns.push(new Column(name, values));
        }
    }

    return columns;
}

class SortOrder {
    private sortOrder: [string, number][] = [];

    add(columnName: string, ascending: boolean): void {
        this.sortOrder = this.sortOrder.filter((it) => it[0] !== columnName);
        this.sortOrder.unshift([columnName, ascending ? 1 : -1]);
    }

    sort(columns: Column[]): void {
        if (columns.length === 0) {
            return;
        }

        let valuesByColumnName: { [columnName: string]: TableValue[] } = {};
        for (let column of columns) {
            valuesByColumnName[column.name] = column.values;
        }

        // Perform an argsort
        function cmp(i: number, j: number): number {
            for (let [columnName, multiplier] of this.sortOrder) {
                let values = valuesByColumnName[columnName];
                if (values === undefined) {
                    // The table's contents must've changed and no longer have a
                    // column with this name
                    continue;
                }

                let a = values[i];
                let b = values[j];

                if (a < b) {
                    return -1 * multiplier;
                } else if (a > b) {
                    return 1 * multiplier;
                }
            }

            return 0;
        }

        let indices = [...columns[0].values.keys()];
        indices.sort(cmp.bind(this));

        // Now that we have the sorted indices, we can use them to reorder the values
        for (let column of columns) {
            column.values = indices.map((i) => column.values[i]);
        }
    }
}

export class TableComponent extends ComponentBase {
    state: TableState;

    private sortOrder = new SortOrder();

    private headerCells: HTMLElement[] = [];
    private rowNumberCells: HTMLElement[] = [];
    private dataCells: HTMLElement[] = [];

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-table');

        return element;
    }

    updateElement(
        deltaState: TableDeltaState,
        latentComponents: Set<ComponentBase>
    ): void {
        if (deltaState.data !== undefined) {
            this.state.data = dataToColumns(deltaState.data);

            this.displayData();

            if (deltaState.show_row_numbers ?? this.state.show_row_numbers) {
                this.showRowNumbers();
            }

            if (Array.isArray(deltaState.data)) {
                this.hideColumnHeaders();
            } else {
                this.showColumnHeaders();
            }
        } else if (
            deltaState.show_row_numbers !== undefined &&
            deltaState.show_row_numbers !== this.state.show_row_numbers
        ) {
            if (deltaState.show_row_numbers) {
                this.showRowNumbers();
            } else {
                this.hideRowNumbers();
            }
        }

        this.makeLayoutDirty();
        [this.naturalWidth, this.naturalHeight] = getElementDimensions(
            this.element
        );
    }

    // Natural size is set in updateElement
    updateNaturalWidth(ctx: LayoutContext): void {}
    updateNaturalHeight(ctx: LayoutContext): void {}

    private displayData(): void {
        for (let element of this.dataCells) {
            element.remove();
        }

        this.dataCells = [];

        let columnNr = 2;
        for (let column of this.state.data) {
            for (let [rowNr, value] of column.values.entries()) {
                let cell = document.createElement('span');
                cell.textContent = `${value}`;
                cell.style.textAlign = column.alignment;

                cell.style.gridRow = `${rowNr + 2}`;
                cell.style.gridColumn = `${columnNr}`;
                this.element.appendChild(cell);
                this.dataCells.push(cell);
            }

            columnNr++;
        }
    }

    private showRowNumbers(): void {
        this.hideRowNumbers();

        let numRows =
            this.state.data.length === 0 ? 0 : this.state.data[0].values.length;

        for (let i = 0; i < numRows; i++) {
            let cell = document.createElement('span');
            cell.textContent = `${i + 1}.`;
            cell.style.textAlign = 'right';
            cell.style.opacity = '0.5';

            cell.style.gridRow = `${i + 2}`;
            cell.style.gridColumn = '1';
            this.element.appendChild(cell);

            this.rowNumberCells.push(cell);
        }
    }

    private hideRowNumbers(): void {
        for (let element of this.rowNumberCells) {
            element.remove();
        }

        this.rowNumberCells = [];
    }

    private showColumnHeaders(): void {
        this.hideColumnHeaders();

        for (let [i, column] of this.state.data.entries()) {
            let cell = document.createElement('span');
            cell.classList.add('header');
            cell.textContent = column.name;
            cell.style.textAlign = column.alignment;
            cell.style.opacity = '0.5';

            cell.addEventListener(
                'click',
                this.onHeaderClick.bind(this, column.name)
            );

            cell.style.gridRow = '1';
            cell.style.gridColumn = `${i + 2}`;
            this.element.appendChild(cell);

            this.headerCells.push(cell);
        }
    }

    private hideColumnHeaders(): void {
        for (let element of this.headerCells) {
            element.remove();
        }

        this.headerCells = [];
    }

    private onHeaderClick(columnName: string, event: MouseEvent): void {
        let clickedHeader = event.target as HTMLElement;
        if (clickedHeader.tagName !== 'SPAN') {
            clickedHeader = clickedHeader.parentElement!;
        }

        let ascending = clickedHeader.dataset.sort !== 'ascending';

        // Remove the `data-sort` attribute from all other headers
        for (let cell of this.headerCells) {
            delete cell.dataset.sort;
        }
        clickedHeader.dataset.sort = ascending ? 'ascending' : 'descending';

        this.sortOrder.add(columnName, ascending);
        this.sortOrder.sort(this.state.data);
        this.displayData();

        // Eat the event
        event.stopPropagation();
    }
}
