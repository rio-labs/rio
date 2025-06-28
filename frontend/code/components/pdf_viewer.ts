import { ComponentStatesUpdateContext } from "../componentManagement";
import { applyIcon } from "../designApplication";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";

export type PdfViewerState = ComponentState & {
    _type_: "PdfViewer-builtin";
    pdfUrl: string;
};

export class PdfViewerComponent extends ComponentBase<PdfViewerState> {
    private objectElement: HTMLObjectElement;
    private fallbackColumn: HTMLElement;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-pdf-viewer");

        // Create an object element for PDF viewing
        this.objectElement = document.createElement("object");
        this.objectElement.type = "application/pdf";
        this.objectElement.setAttribute("aria-label", "PDF document");
        element.appendChild(this.objectElement);

        // Add fallback content, should the object element fail to load
        this.fallbackColumn = document.createElement("div");
        this.fallbackColumn.classList.add("rio-pdf-viewer-fallback");
        this.objectElement.appendChild(this.fallbackColumn);

        let iconElement = document.createElement("div");
        this.fallbackColumn.appendChild(iconElement);
        applyIcon(iconElement, "material/error", "danger");

        let textElement = document.createElement("div");
        textElement.innerHTML = `The PDF document cannot be displayed in your browser.<br>You can try to <a href="${this.state.pdfUrl}" download target="_blank">download</a> it instead.`;
        this.fallbackColumn.appendChild(textElement);

        return element;
    }

    updateElement(
        deltaState: DeltaState<PdfViewerState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        if (
            deltaState.pdfUrl !== undefined &&
            this.objectElement.data !== deltaState.pdfUrl
        ) {
            // Update the PDF source
            this.objectElement.data = deltaState.pdfUrl;
        }
    }
}
