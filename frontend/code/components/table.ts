import { markEventAsHandled } from '../eventHandling';
import { ComponentBase, ComponentState } from './componentBase';

type TableValue = number | string;

type TableStyle = {
    left: number;
    top: number | 'header';
    width: number;
    height: number;

    fontWeight?: 'normal' | 'bold';
};

type TableState = ComponentState & {
    _type_: 'Table-builtin';
    show_row_numbers?: boolean;
    headers?: string[] | null;
    data?: TableValue[][];
    styling?: TableStyle[];
};

export class TableComponent extends ComponentBase {
    state: Required<TableState>;

    private tableElement: HTMLElement;

    private dataWidth: number;
    private dataHeight: number;

    createElement(): HTMLElement {
        let element = document.createElement('div');

        this.tableElement = document.createElement('div');
        this.tableElement.classList.add('rio-table');
        element.appendChild(this.tableElement);

        return element;
    }

    updateElement(
        deltaState: TableState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        // Content
        if (deltaState.data !== undefined) {
            console.log(`Headers ${deltaState.headers}`);
            console.log(`Data ${deltaState.data}`);
            this.updateContent();
        }

        // Anything else requires a styling update
        this.updateStyling();
    }

    /// Removes any previous content and updates the table with the new data.
    /// Does not apply any sort of styling, not even to the headers or row
    /// numbers.
    private updateContent(): void {
        // Clear the old table
        this.tableElement.innerHTML = '';

        // If there is no data, this is it
        if (this.state.data.length === 0) {
            return;
        }

        this.dataHeight = this.state.data.length;
        this.dataWidth = this.state.data[0].length;

        // Update the table's CSS to match the number of rows & columns
        this.tableElement.style.gridTemplateColumns = `repeat(${
            this.dataWidth + 1
        }, auto)`;

        this.tableElement.style.gridTemplateRows = `repeat(${
            this.dataHeight + 1
        }, auto)`;

        // Empty top-left corner
        let itemElement = document.createElement('div');
        itemElement.classList.add('rio-table-header');
        itemElement.textContent = '';
        this.tableElement.appendChild(itemElement);

        // Add the headers
        let headers: string[];

        if (this.state.headers === null) {
            headers = new Array(this.dataWidth).fill('');
        } else {
            headers = this.state.headers;
        }

        for (let ii = 0; ii < this.dataWidth; ii++) {
            let itemElement = document.createElement('div');
            itemElement.classList.add('rio-table-header');
            itemElement.textContent = headers[ii];
            this.tableElement.appendChild(itemElement);
        }

        // Add the cells
        for (let data_yy = 0; data_yy < this.dataHeight; data_yy++) {
            // Row number
            let itemElement = document.createElement('div');
            itemElement.classList.add('rio-table-row-number');
            itemElement.textContent = (data_yy + 1).toString();
            this.tableElement.appendChild(itemElement);

            // Data value
            for (let data_xx = 0; data_xx < this.dataWidth; data_xx++) {
                let itemElement = document.createElement('div');
                itemElement.classList.add('rio-table-item');
                itemElement.textContent =
                    this.state.data[data_yy][data_xx].toString();
                this.tableElement.appendChild(itemElement);
            }
        }

        // Add row-highlighters. These span entire rows and change colors when
        // hovered
        for (let ii = 0; ii < this.dataHeight; ii++) {
            let itemElement = document.createElement('div');
            itemElement.classList.add('rio-table-row-highlighter');
            itemElement.style.gridRow = `${ii + 2}`;
            itemElement.style.gridColumn = `1 / span ${this.dataWidth + 1}`;
            this.tableElement.appendChild(itemElement);
        }
    }

    /// Updates the styling of the already populated table.
    private updateStyling(): void {
        for (let style of this.state.styling) {
            this.applySingleStyle(style);
        }
    }

    private applySingleStyle(style: TableStyle): void {
        // Come up with the CSS to apply to the targeted cells
        let css = {};

        if (style.fontWeight !== undefined) {
            css['font-weight'] = style.fontWeight;
        }

        // Find the targeted area
        let styleLeft = style.left + 1;
        let styleWidth = style.width;
        let styleTop = style.top === 'header' ? 0 : style.top + 1;
        let styleHeight = style.height;

        let htmlWidth = this.dataWidth + 1;

        // Apply the CSS to all selected cells
        for (let yy = styleTop; yy < styleTop + styleHeight; yy++) {
            for (let xx = styleLeft; xx < styleLeft + styleWidth; xx++) {
                let index = yy * htmlWidth + xx;
                let cell = this.tableElement.children[index] as HTMLElement;

                Object.assign(cell.style, css);
            }
        }
    }
}
