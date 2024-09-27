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
    data?: TableValue[][];
    styling?: TableStyle[];
};

export class TableComponent extends ComponentBase {
    state: Required<TableState>;

    private tableElement: HTMLElement;

    private dataWidth: number;
    private dataHeight: number;

    createElement(): HTMLElement {
        let element = document.createElement("div");

        this.tableElement = document.createElement("div");
        this.tableElement.classList.add("rio-table");
        element.appendChild(this.tableElement);

        return element;
    }

    updateElement(
        deltaState: TableState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        var styleNeedsClearing = true;

        // Content
        if (deltaState.data !== undefined) {
            this.updateContent();

            // Since the content was completely replaced, there is no need to
            // walk over all cells and clear their styling
            styleNeedsClearing = false;
        }

        // Anything else requires a styling update
        if (styleNeedsClearing) {
            this.clearStyling();
        }

        this.updateStyling();
    }

    private onEnterCell(element: HTMLElement, xx: number, yy: number): void {
        for (let ii = 0; ii <= this.dataWidth; ii++) {
            let cell = this.getCellElement(ii, yy);
            cell.style.backgroundColor = "var(--rio-local-bg-active)";

            if (ii == 0 && ii == this.dataWidth) {
                cell.style.borderRadius =
                    "var(--rio-global-corner-radius-small)";
            } else if (ii == 0) {
                cell.style.borderRadius =
                    "var(--rio-global-corner-radius-small) 0 0 var(--rio-global-corner-radius-small)";
            } else if (ii == this.dataWidth) {
                cell.style.borderRadius =
                    "0 var(--rio-global-corner-radius-small) var(--rio-global-corner-radius-small) 0";
            }
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
        let itemElement = document.createElement("div");
        itemElement.classList.add("rio-table-header");
        itemElement.textContent = "";
        this.tableElement.appendChild(itemElement);

        // Helper function for adding elements
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

            addElement(itemElement, "rio-table-header", ii + 2, 1, 1, 1);
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
                data_yy + 2,
                1,
                1
            );

            // Data value
            for (let data_xx = 0; data_xx < this.dataWidth; data_xx++) {
                let itemElement = document.createElement("div");
                itemElement.classList.add("rio-table-item");
                itemElement.textContent =
                    this.state.data[data_yy][data_xx].toString();

                addElement(
                    itemElement,
                    "rio-table-item",
                    data_xx + 2,
                    data_yy + 2,
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

            cellElement.addEventListener("mouseenter", () => {
                this.onEnterCell(cellElement, xx, yy);
            });

            cellElement.addEventListener("mouseleave", () => {
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
