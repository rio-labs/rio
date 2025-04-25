import { ComponentStatesUpdateContext } from "../componentManagement";
import { colorToCssString } from "../cssUtils";
import { Color } from "../dataModels";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";

type TableValue = number | string;

type TableStyle = {
    left: number;
    top: number | "header";
    width: number;
    height: number;

    fontColor?: Color;
    backgroundColor?: Color;
    italic?: boolean;
    fontWeight?: "normal" | "bold";
    justify?: "left" | "center" | "right";
};

type TableState = ComponentState & {
    _type_: "Table-builtin";
    show_row_numbers: boolean;
    headers: string[] | null;
    columns: TableValue[][];
    styling: TableStyle[];
    reportPress: boolean;
};

export class TableComponent extends ComponentBase<TableState> {
    private dataWidth: number;
    private dataHeight: number;

    private totalWidth: number;
    private totalHeight: number;

    /// The same as the columns stored in the state, but transposed. Columns are
    /// more efficient for Python to work with, but for sorting and filtering
    /// rows work better.
    private rows: TableValue[][];

    // False if the component has never been updated before
    private isInitialized: boolean = false;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-table");
        return element;
    }

    /// Transposes the given columns into rows
    columnsToRows(columns: TableValue[][]): TableValue[][] {
        let rows: TableValue[][] = [];

        if (columns.length === 0) {
            return rows;
        }

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
        deltaState: DeltaState<TableState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        // If true, all HTML content of the table will be cleared and replaced
        let contentNeedsRepopulation = false;

        // If true, the table's styling will be cleared before applying the new
        // styling
        var styleNeedsClearing = true;

        // If this is the first time running, the content obviously must be
        // populated. This check is necessary, because in this case the `state`
        // and `deltaState` are the same, and so any checks for differences
        // would be negative.
        if (!this.isInitialized) {
            contentNeedsRepopulation = true;
        }

        // Store the new headers. This is needed because called functions might
        // reference `this.state` rather than `deltaState`.
        if (deltaState.headers !== undefined) {
            // Expose whether there's a header to CSS
            this.element.classList.toggle(
                "rio-table-with-headers",
                deltaState.headers !== null
            );

            // Update the table's content
            contentNeedsRepopulation = true;
        }

        // Columns / Data / Rows
        if (deltaState.columns !== undefined) {
            // Store the data in the preferred row-major format
            this.rows = this.columnsToRows(deltaState.columns);

            // Update the table's content
            contentNeedsRepopulation = true;
        }

        // Show row numbers?
        if (deltaState.show_row_numbers !== undefined) {
            this.element.classList.toggle(
                "rio-table-with-row-numbers",
                deltaState.show_row_numbers
            );

            // Update the table's content
            contentNeedsRepopulation = true;
        }

        // Repopulate the HTML
        if (contentNeedsRepopulation) {
            Object.assign(this.state, deltaState);
            this.updateContent();

            // Since this is completely fresh HTML there is no need to clear
            // any styling
            styleNeedsClearing = false;
        }

        // Do previously applied styles need clearing?
        if (styleNeedsClearing) {
            if (deltaState.styling !== undefined) {
                this.state.styling = deltaState.styling;
            }

            this.clearStyling();
        }

        // Apply the new styling
        if (contentNeedsRepopulation || styleNeedsClearing) {
            this.updateStyling();
        }

        // This component has now been initialized
        this.isInitialized = true;
    }

    private onEnterCell(element: HTMLElement, xx: number, yy: number): void {
        // Don't colorize the header
        if (yy === 0 && this.state.headers !== null) {
            return;
        }

        // Otherwise highlight the entire row
        for (let ii = 0; ii < this.totalWidth; ii++) {
            let cell = this.getCellElement(ii, yy);
            cell.style.backgroundColor = "var(--rio-local-bg-active)";
        }
    }

    private onLeaveCell(element: HTMLElement, xx: number, yy: number): void {
        for (let ii = 0; ii < this.totalWidth; ii++) {
            // Remove the hover style. This can't just delete the property, as
            // the cell might have had a style applied.
            let cell = this.getCellElement(ii, yy);
            cell.style.removeProperty("background-color");
        }
    }

    /// Removes any previous content and updates the table with the new data.
    /// Does not apply any sort of styling, not even to the headers or row
    /// numbers.
    private updateContent(): void {
        // Remove any old HTML
        this.element.innerHTML = "";

        // Update the data dimensions. These will be used throughout the
        // function.
        let headersOffset = this.state.headers === null ? 0 : 1;
        let rowNumbersOffset = this.state.show_row_numbers ? 1 : 0;

        this.dataHeight = this.rows.length;

        if (this.dataHeight === 0) {
            if (this.state.headers === null) {
                this.dataWidth = 0;
            } else {
                this.dataWidth = this.state.headers.length;
            }
        } else {
            this.dataWidth = this.rows[0].length;
        }

        this.totalWidth = this.dataWidth + rowNumbersOffset;
        this.totalHeight = this.dataHeight + headersOffset;

        // Update the table's CSS to match the number of rows & columns
        this.element.style.gridTemplateColumns = `repeat(${this.totalWidth}, auto)`;
        this.element.style.gridTemplateRows = `repeat(${this.totalHeight}, auto)`;

        // Helper function for adding elements
        //
        // All coordinates are 0-based. The top-left cell is (0, 0). This
        // doesn't account for the header or row number cells.
        let addElement = (
            element: HTMLElement,
            cssClasses: string[],
            left: number,
            top: number
        ) => {
            const width = 1;
            const height = 1;

            let area = `${top + 1} / ${left + 1} / ${top + height} / ${
                left + width
            }`;
            element.style.gridArea = area;
            element.classList.add(...cssClasses);
            this.element.appendChild(element);
        };

        // Add the headers
        if (this.state.headers !== null) {
            if (this.state.show_row_numbers) {
                let itemElement = document.createElement("div");
                itemElement.textContent = "";
                addElement(
                    itemElement,
                    ["rio-table-header", "rio-table-row-number"],
                    0,
                    0
                );
            }

            for (let ii = 0; ii < this.dataWidth; ii++) {
                let itemElement = document.createElement("div");
                itemElement.textContent = this.state.headers[ii];

                // Add click handler if press events are requested
                if (this.state.reportPress) {
                    itemElement.addEventListener("click", (e) => {
                        this._sendCellPressEvent("press", ii, "header");
                    });
                    // Add pointer style to indicate it's clickable
                    itemElement.style.cursor = "pointer";
                }

                addElement(
                    itemElement,
                    ["rio-table-header"],
                    ii + rowNumbersOffset,
                    0
                );
            }
        }

        // Add the cells
        for (let data_yy = 0; data_yy < this.dataHeight; data_yy++) {
            // Row number
            if (this.state.show_row_numbers) {
                let itemElement = document.createElement("div");
                itemElement.textContent = (data_yy + 1).toString();

                addElement(
                    itemElement,
                    ["rio-table-row-number"],
                    0,
                    data_yy + headersOffset
                );
            }

            // Data value
            for (let data_xx = 0; data_xx < this.dataWidth; data_xx++) {
                let itemElement = document.createElement("div");
                itemElement.classList.add("rio-table-cell");
                itemElement.textContent =
                    this.rows[data_yy][data_xx].toString();

                // Add click handler if press events are requested
                if (this.state.reportPress) {
                    itemElement.addEventListener("click", (e) => {
                        this._sendCellPressEvent("press", data_xx, data_yy);
                    });
                    // Add pointer style to indicate it's clickable
                    itemElement.style.cursor = "pointer";
                }

                addElement(
                    itemElement,
                    ["rio-table-cell"],
                    data_xx + rowNumbersOffset,
                    data_yy + headersOffset
                );
            }
        }

        // Round the corners of the table
        if (this.totalWidth !== 0 && this.totalHeight !== 0) {
            let topLeft = this.getCellElement(0, 0);
            let topRight = this.getCellElement(this.totalWidth - 1, 0);
            let bottomLeft = this.getCellElement(0, this.totalHeight - 1);
            let bottomRight = this.getCellElement(
                this.totalWidth - 1,
                this.totalHeight - 1
            );

            let radiusCss = "var(--rio-global-corner-radius-medium)";
            topLeft.style.borderTopLeftRadius = radiusCss;
            topRight.style.borderTopRightRadius = radiusCss;
            bottomLeft.style.borderBottomLeftRadius = radiusCss;
            bottomRight.style.borderBottomRightRadius = radiusCss;
        }

        // Subscribe to events
        for (let ii = 0; ii < this.element.children.length; ii++) {
            let xx = ii % this.totalWidth;
            let yy = Math.floor(ii / this.totalWidth);
            let cellElement = this.element.children[ii] as HTMLElement;

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
        let index = yy * this.totalWidth + xx;
        return this.element.children[index] as HTMLElement;
    }

    /// Removes any styling from the table
    private clearStyling(): void {
        for (let rawCell of this.element.children) {
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
        let css: { [key: string]: string } = {};
        let customVars: { [key: string]: string } = {};

        if (style.fontColor !== undefined) {
            css["color"] = colorToCssString(style.fontColor);
        }

        if (style.backgroundColor !== undefined) {
            // The background color is also changed for highlighting the row
            // when hovered. Just assigning it here would thus be overridden by
            // the hover effect. To prevent this assign the color to a variable
            // instead. The actual cell style can then use that variable.
            customVars["--rio-table-background-color"] = colorToCssString(
                style.backgroundColor
            );
        }

        if (style.italic !== undefined) {
            css["font-style"] = style.italic ? "italic" : "normal";
        }

        if (style.fontWeight !== undefined) {
            css["font-weight"] = style.fontWeight;
        }

        if (style.justify !== undefined) {
            let justification = {
                left: "start",
                center: "center",
                right: "end",
            }[style.justify];

            // For some reason, cells with multi-line text don't respect
            // `justify-content`. `text-align` similarly is not respected by
            // everyone. So we have to use both.
            css["text-align"] = css["justify-content"] = justification;
        }

        // Find the targeted area
        let headersOffset = this.state.headers === null ? 0 : 1;
        let rowNumbersOffset = this.state.show_row_numbers ? 1 : 0;

        let styleLeft = style.left + rowNumbersOffset;
        let styleWidth = style.width;
        let styleTop = style.top === "header" ? 0 : style.top + headersOffset;
        let styleHeight = style.height;

        // Apply the CSS to all selected cells
        for (let yy = styleTop; yy < styleTop + styleHeight; yy++) {
            for (let xx = styleLeft; xx < styleLeft + styleWidth; xx++) {
                let cell = this.getCellElement(xx, yy);
                Object.assign(cell.style, css);

                // `Object.assign` does not work for custom properties
                for (let [key, value] of Object.entries(customVars)) {
                    cell.style.setProperty(key, value);
                }
            }
        }
    }

    /// Sends a cell press event to the backend
    private _sendCellPressEvent(
        eventType: string,
        column: number,
        row: number | "header"
    ): void {
        this.sendMessageToBackend({
            type: eventType,
            column: column,
            row: row,
        });
    }
}
