import { markEventAsHandled } from "../eventHandling";
import { ComponentBase, ComponentState } from "./componentBase";

type TableValue = number | string;

type TableStyle = {
    left: number;
    top: number | "header";
    width: number;
    height: number;

    fontWeight?: "normal" | "bold";
};

type TableState = ComponentState & {
    _type_: "Table-builtin";
    show_row_numbers?: boolean;
    headers?: string[] | null;
    columns?: TableValue[][];
    styling?: TableStyle[];
};

export class TableComponent extends ComponentBase {
    declare state: Required<TableState>;

    private tableElement: HTMLElement;

    private dataWidth: number;
    private dataHeight: number;

    /// The same as the columns stored in the state, but transposed. Columns are
    /// more efficient for Python to work with, but for sorting and filtering
    /// rows work better.
    private rows: TableValue[][];

    createElement(): HTMLElement {
        let element = document.createElement("div");

        this.tableElement = document.createElement("div");
        this.tableElement.classList.add("rio-table");
        element.appendChild(this.tableElement);

        return element;
    }

    /// Transposes the given columns into rows
    columnsToRows(columns: TableValue[][]): TableValue[][] {
        let rows: TableValue[][] = [];

        for (let xx = 0; xx < columns[0].length; xx++) {
            let row: TableValue[] = [];

            for (let yy = 0; yy < columns.length; yy++) {
                row.push(columns[yy][xx]);
            }

            rows.push(row);
        }

        return rows;
    }

    updateElement(
        deltaState: TableState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        var styleNeedsClearing = true;

        // Content
        if (deltaState.columns !== undefined) {
            // Store the data in the preferred row-major format
            this.rows = this.columnsToRows(this.state.columns);

            // Delete the old columns to avoid storing all values twice
            // deltaState._columns = undefined;

            // Make the HTML match the new data
            this.updateContent();

            // Since the content was completely replaced, there is no need to
            // walk over all cells and clear their styling
            styleNeedsClearing = false;

            // Expose whether there's a header to CSS
            this.element.classList.toggle(
                "rio-table-with-header",
                this.state.headers !== null
            );
        }

        // Show row numbers?
        if (deltaState.show_row_numbers !== undefined) {
            this.element.classList.toggle(
                "rio-table-with-row-numbers",
                this.state.show_row_numbers
            );
        }

        // Do previously applied styles need clearing?
        if (styleNeedsClearing) {
            this.clearStyling();
        }

        this.updateStyling();
    }

    private onEnterCell(element: HTMLElement, xx: number, yy: number): void {
        // Don't colorize the header
        if (yy === 0) {
            return;
        }

        // Otherwise highlight the entire row
        for (let ii = 0; ii <= this.dataWidth; ii++) {
            let cell = this.getCellElement(ii, yy);
            cell.style.backgroundColor = "var(--rio-local-bg-active)";
        }
    }

    private onLeaveCell(element: HTMLElement, xx: number, yy: number): void {
        for (let ii = 0; ii <= this.dataWidth; ii++) {
            let cell = this.getCellElement(ii, yy);
            cell.style.removeProperty("background-color");
        }
    }

    /// Removes any previous content and updates the table with the new data.
    /// Does not apply any sort of styling, not even to the headers or row
    /// numbers.
    private updateContent(): void {
        // Clear the old table
        this.tableElement.innerHTML = "";

        // If there is no data, this is it
        if (this.rows.length === 0) {
            return;
        }

        this.dataHeight = this.rows.length;
        this.dataWidth = this.rows[0].length;

        // Update the table's CSS to match the number of rows & columns
        this.tableElement.style.gridTemplateColumns = `repeat(${
            this.dataWidth + 1
        }, auto)`;

        this.tableElement.style.gridTemplateRows = `repeat(${
            this.dataHeight + 1
        }, auto)`;

        // Empty top-left corner
        let itemElement = document.createElement("div");
        itemElement.classList.add("rio-table-header", "rio-table-row-number");
        itemElement.textContent = "";
        this.tableElement.appendChild(itemElement);

        // Helper function for adding elements
        //
        // All coordinates are 0-based. The top-left cell is (0, 0).
        let addElement = (
            element: HTMLElement,
            cssClass: string,
            left: number,
            top: number,
            width: number,
            height: number
        ) => {
            let area = `${top} / ${left} / ${top + height} / ${left + width}`;
            element.style.gridArea = area;
            element.classList.add(cssClass);
            this.tableElement.appendChild(element);

            // Add additional CSS classes based on where in the table the cell
            // is
            if (left === 1) {
                element.classList.add("rio-table-first-column");
            }

            if (top === 1) {
                element.classList.add("rio-table-first-row");
            }

            if (left + width === this.dataWidth + 1) {
                element.classList.add("rio-table-last-column");
            }

            if (top + height === this.dataHeight + 1) {
                element.classList.add("rio-table-last-row");
            }
        };

        // Add the headers
        let headers: string[];

        if (this.state.headers === null) {
            headers = new Array(this.dataWidth).fill("");
        } else {
            headers = this.state.headers;
        }

        for (let ii = 0; ii < this.dataWidth; ii++) {
            let itemElement = document.createElement("div");
            itemElement.textContent = headers[ii];

            addElement(itemElement, "rio-table-header", ii + 1, 1, 1, 1);
        }

        // Add the cells
        for (let data_yy = 0; data_yy < this.dataHeight; data_yy++) {
            // Row number
            let itemElement = document.createElement("div");
            itemElement.textContent = (data_yy + 1).toString();

            addElement(
                itemElement,
                "rio-table-row-number",
                1,
                data_yy + 1,
                1,
                1
            );

            // Data value
            for (let data_xx = 0; data_xx < this.dataWidth; data_xx++) {
                let itemElement = document.createElement("div");
                itemElement.classList.add("rio-table-item");
                itemElement.textContent =
                    this.rows[data_yy][data_xx].toString();

                addElement(
                    itemElement,
                    "rio-table-item",
                    data_xx + 1,
                    data_yy + 1,
                    1,
                    1
                );
            }
        }

        // Subscribe to events
        let htmlWidth = this.dataWidth + 1;

        for (let ii = 0; ii < this.tableElement.children.length; ii++) {
            let xx = ii % htmlWidth;
            let yy = Math.floor(ii / htmlWidth);
            let cellElement = this.tableElement.children[ii] as HTMLElement;

            cellElement.addEventListener("pointerenter", () => {
                this.onEnterCell(cellElement, xx, yy);
            });

            cellElement.addEventListener("pointerleave", () => {
                this.onLeaveCell(cellElement, xx, yy);
            });
        }
    }

    /// Gets the HTML element that corresponds to the given cell. Indexing
    /// includes the header and row number cells, and so is offset by one from
    /// the data index.
    private getCellElement(xx: number, yy: number): HTMLElement {
        let htmlWidth = this.dataWidth + 1;
        let index = yy * htmlWidth + xx;
        return this.tableElement.children[index] as HTMLElement;
    }

    /// Removes any styling from the table
    private clearStyling(): void {
        for (let rawCell of this.tableElement.children) {
            let cell = rawCell as HTMLElement;
            cell.style.cssText = "";
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
            css["font-weight"] = style.fontWeight;
        }

        // Find the targeted area
        let styleLeft = style.left + 1;
        let styleWidth = style.width;
        let styleTop = style.top === "header" ? 0 : style.top + 1;
        let styleHeight = style.height;

        // Apply the CSS to all selected cells
        for (let yy = styleTop; yy < styleTop + styleHeight; yy++) {
            for (let xx = styleLeft; xx < styleLeft + styleWidth; xx++) {
                let cell = this.getCellElement(xx, yy);
                Object.assign(cell.style, css);
            }
        }
    }
}
