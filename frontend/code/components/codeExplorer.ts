import hljs from "highlight.js/lib/common";
import {
    componentsByElement,
    componentsById,
    ComponentStatesUpdateContext,
} from "../componentManagement";
import { ComponentId } from "../dataModels";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { applyIcon } from "../designApplication";

export type CodeExplorerState = ComponentState & {
    _type_: "CodeExplorer-builtin";
    source_code: string;
    build_result: ComponentId;
    line_indices_to_component_keys: (string | number | null)[];
    style: "horizontal" | "vertical";
};

export class CodeExplorerComponent extends ComponentBase<CodeExplorerState> {
    private sourceCodeElement: HTMLElement;
    private arrowElement: HTMLElement;
    private buildResultElement: HTMLElement;

    private sourceHighlighterElement: HTMLElement;
    private resultHighlighterElement: HTMLElement;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        // Build the HTML
        let element = document.createElement("div");
        element.classList.add("rio-code-explorer");

        element.innerHTML = `
            <div class="rio-code-explorer-source-code"></div>
            <div class="rio-code-explorer-arrow"></div>
            <div class="rio-code-explorer-build-result"></div>
        `;

        this.sourceHighlighterElement = document.createElement("div");
        this.sourceHighlighterElement.classList.add(
            "rio-code-explorer-highlighter"
        );

        this.resultHighlighterElement = document.createElement("div");
        this.resultHighlighterElement.classList.add(
            "rio-code-explorer-highlighter"
        );

        // Expose the elements
        [this.sourceCodeElement, this.arrowElement, this.buildResultElement] =
            Array.from(element.children) as HTMLElement[];

        // Listen for pointer events
        this.buildResultElement.addEventListener(
            "pointermove",
            this.onResultPointerMove.bind(this),
            { capture: true }
        );

        this.buildResultElement.addEventListener("pointerleave", () => {
            this._highlightComponentByKey(null);
        });

        return element;
    }

    updateElement(
        deltaState: DeltaState<CodeExplorerState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        // Update the source
        if (deltaState.source_code !== undefined) {
            let hlResult = hljs.highlight(deltaState.source_code, {
                language: "python",
                ignoreIllegals: true,
            });
            this.sourceCodeElement.innerHTML = hlResult.value;

            // Connect event handlers
            this._connectHighlightEventListeners();

            // Re-add the highlighter
            this.sourceCodeElement.appendChild(this.sourceHighlighterElement);
        }

        // Update the child
        if (deltaState.build_result !== undefined) {
            // Remove the highlighter prior to removing the child, as
            // `replaceOnlyChild` expects there to be at most one element
            this.resultHighlighterElement.remove();

            // Update the child
            this.replaceOnlyChild(
                context,
                deltaState.build_result,
                this.buildResultElement
            );

            // Position it, so this doesn't happen every time during layouting
            let buildResultElement = componentsById[deltaState.build_result]!;
            buildResultElement.element.style.removeProperty("left");
            buildResultElement.element.style.removeProperty("top");

            // (Re-)Add the highlighter
            this.buildResultElement.appendChild(this.resultHighlighterElement);
        }

        if (deltaState.style !== undefined) {
            if (deltaState.style === "horizontal") {
                this.element.style.flexDirection = "row";
                applyIcon(
                    this.arrowElement,
                    "material/arrow_right_alt:fill",
                    "var(--rio-global-primary-bg)"
                );
            } else {
                this.element.style.flexDirection = "column";
                applyIcon(
                    this.arrowElement,
                    "material/arrow_downward:fill",
                    "var(--rio-global-primary-bg)"
                );
            }
        }
    }

    private _connectHighlightEventListeners(): void {
        // The text is a mix of spans and raw text. Some of them may extend over
        // multiple lines. Split them up, and use this opportunity to wrap all
        // text in spans as well.
        let lineIndex = 0;

        let elementsBefore = Array.from(this.sourceCodeElement.childNodes);
        this.sourceCodeElement.innerHTML = "";

        for (let element of elementsBefore) {
            // If this is just a plain text element, wrap it in a span
            let multiSpan: HTMLSpanElement;

            if (element instanceof Text) {
                let span = document.createElement("span");
                span.textContent = element.textContent!;
                multiSpan = span;
            } else {
                console.assert(
                    element instanceof HTMLSpanElement,
                    `${element} is not a HTMLSpanElement`
                );
                multiSpan = element as HTMLSpanElement;
            }

            // Re-add the spans, keeping track of the line
            let lines = multiSpan.textContent!.split("\n");

            for (let ii = 0; ii < lines.length; ii++) {
                if (ii !== 0) {
                    lineIndex += 1;
                    this.sourceCodeElement.appendChild(
                        document.createTextNode("\n")
                    );
                }

                let singleSpan = multiSpan.cloneNode() as HTMLSpanElement;
                singleSpan.innerText = lines[ii];
                singleSpan.dataset.lineIndex = lineIndex.toString();
                this.sourceCodeElement.appendChild(singleSpan);

                // Add the event listeners
                ((currentLineIndex) => {
                    singleSpan.addEventListener("pointerenter", () => {
                        this.onLineEntered(currentLineIndex);
                    });
                })(lineIndex);

                singleSpan.addEventListener("pointerleave", () => {
                    this.onLineEntered(null);
                });

                // Indicate to the user that the element is interactive
                singleSpan.style.cursor = "crosshair";
            }
        }
    }

    private onLineEntered(lineIndex: number | null): void {
        let key: string | number | null = null;

        // Which key should be highlighted?
        if (lineIndex !== null) {
            key = this.state.line_indices_to_component_keys[lineIndex];
        }

        // Pass control to the highlight functions
        this._highlightComponentByKey(key);
    }

    private onResultPointerMove(event: PointerEvent): void {
        // Find the element that's being hovered over
        let curElement = event.target as HTMLElement;

        // Find the component which owns this element
        let targetComponentKey: string | number | null;

        while (true) {
            // Don't look outside of the build result
            if (curElement === this.buildResultElement) {
                targetComponentKey = null;
                break;
            }

            // Is this a component's root element?
            let targetComponent = componentsByElement.get(curElement);

            // If a component was found, make sure it also has a key
            if (
                targetComponent !== undefined &&
                targetComponent.state.key !== null
            ) {
                targetComponentKey = targetComponent.state.key;
                break;
            }

            // Nope, keep going
            curElement = curElement.parentElement!;
        }

        // Highlight the target
        this._highlightComponentByKey(targetComponentKey);
    }

    private _highlightComponentByKey(key: string | number | null): void {
        // Nothing to highlight?
        if (key === null) {
            this.sourceHighlighterElement.style.opacity = "0";
            this.resultHighlighterElement.style.opacity = "0";
            return;
        }

        // Find the lines corresponding to this component
        let firstLineIndex = 999999,
            lastLineIndex = -1;

        for (
            let ii = 0;
            ii < this.state.line_indices_to_component_keys.length;
            ii++
        ) {
            if (this.state.line_indices_to_component_keys[ii] === key) {
                firstLineIndex = Math.min(firstLineIndex, ii);
                lastLineIndex = Math.max(lastLineIndex, ii);
            }
        }

        // Highlight those lines
        this._highlightLines(firstLineIndex, lastLineIndex);

        // Highlight the result component
        this._highlightKey(key);
    }

    private _highlightLines(
        firstLineIndex: number,
        lastLineIndex: number
    ): void {
        // Determine the area to highlight
        let top = 99999;
        let bottom = -1;

        for (let child of this.sourceCodeElement.children) {
            // Is this child relevant?
            if (!(child instanceof HTMLSpanElement)) {
                continue;
            }

            let lineIndex = parseInt(child.dataset.lineIndex!);
            if (lineIndex < firstLineIndex || lineIndex > lastLineIndex) {
                continue;
            }

            // Yes, update the area
            let childRect = child.getBoundingClientRect();
            top = Math.min(top, childRect.top);
            bottom = Math.max(bottom, childRect.bottom);
        }

        // Don't highlight nonsense if nothing was found
        if (bottom === -1) {
            this.sourceHighlighterElement.style.opacity = "0";
            return;
        }

        // Convert the coordinates to be relative to source code area
        let sourceCodeRect = this.sourceCodeElement.getBoundingClientRect();
        top -= sourceCodeRect.top;
        bottom -= sourceCodeRect.top;

        // Highlight that area
        this.sourceHighlighterElement.style.left = `0`;
        this.sourceHighlighterElement.style.top = `${top}px`;
        this.sourceHighlighterElement.style.right = `0`;
        this.sourceHighlighterElement.style.height = `${bottom - top}px`;

        // Show the highlighter
        this.sourceHighlighterElement.style.opacity = "1";
    }

    private _highlightKey(key: string | number): void {
        // Find the component to highlight
        let targetComponent;
        if (key !== null) {
            targetComponent = this.findComponentByKey(
                componentsById[this.state.build_result]!,
                key
            );

            if (targetComponent === null) {
                console.error(
                    `CodeExplorer could not find component with key ${key}`
                );
                return;
            }
        }

        // Highlight the target
        let rootRect = this.buildResultElement.getBoundingClientRect();
        let targetRect = targetComponent.element.getBoundingClientRect();

        // If the highlighter is currently completely invisible, teleport it.
        // Make sure to check the computed, current opacity, since it's animated
        let teleport =
            getComputedStyle(this.resultHighlighterElement).opacity == "0"; // Note the == instead of ===

        // FIXME: Teleport isn't working
        // if (teleport) {
        //     disableTransitions(this.highlighterElement);
        //     commitCss(this.highlighterElement);
        // }

        this.resultHighlighterElement.style.left = `${
            targetRect.left - rootRect.left
        }px`;
        this.resultHighlighterElement.style.top = `${
            targetRect.top - rootRect.top
        }px`;
        this.resultHighlighterElement.style.width = `${targetRect.width}px`;
        this.resultHighlighterElement.style.height = `${targetRect.height}px`;

        // enableTransitions(this.highlighterElement);

        this.resultHighlighterElement.style.opacity = "1";
    }

    private findComponentByKey(
        currentComponent: ComponentBase,
        key: string | number
    ): ComponentBase | null {
        // Found it?
        if (currentComponent.state.key === key) {
            return currentComponent;
        }

        // Nope, recurse
        for (let child of currentComponent.children) {
            let result = this.findComponentByKey(child, key);

            if (result !== null) {
                return result;
            }
        }

        // Exhausted all children
        return null;
    }
}
