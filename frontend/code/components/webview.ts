import { ComponentStatesUpdateContext } from "../componentManagement";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";

export type WebviewState = ComponentState & {
    _type_: "Webview-builtin";
    content: string; // Url or Html code
    enable_pointer_events: boolean;
    resize_to_fit_content: boolean;
};

export class WebviewComponent extends ComponentBase<WebviewState> {
    private iframe: HTMLIFrameElement | null = null;
    private resizeObserver: ResizeObserver | null = null;
    private isInitialized = false;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-webview");
        return element;
    }

    updateElement(
        deltaState: DeltaState<WebviewState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        if (deltaState.content !== undefined) {
            // If the URL/HTML hasn't actually changed from last time, don't do
            // anything. This is important so scripts don't get re-executed each
            // time the component is updated.
            if (
                deltaState.content !== this.state.content ||
                !this.isInitialized
            ) {
                if (isUrl(deltaState.content)) {
                    this.element.innerHTML = "";

                    this.iframe = this.createIframe();
                    this.iframe.src = deltaState.content;

                    this.element.appendChild(this.iframe);
                } else if (requiresIframe(deltaState.content)) {
                    this.element.innerHTML = "";

                    this.iframe = this.createIframe();
                    this.iframe.srcdoc = deltaState.content;

                    this.element.appendChild(this.iframe);
                } else {
                    // Clean up stuff we no longer need
                    this.iframe = null;
                    this.resizeObserver = null;

                    // Load the HTML
                    this.element.innerHTML = deltaState.content;

                    // Just setting the innerHTML doesn't run scripts. Do that manually.
                    this.runScriptsInElement();
                }

                this.isInitialized = true;
            }
        }

        if (deltaState.enable_pointer_events !== undefined) {
            this.element.style.pointerEvents = deltaState.enable_pointer_events
                ? "auto"
                : "none";
        }

        if (
            deltaState.resize_to_fit_content !== undefined &&
            this.iframe !== null
        ) {
            if (deltaState.resize_to_fit_content) {
                if (this.resizeObserver === null) {
                    this.resizeObserver = tryCreateIframeResizeObserver(
                        this.iframe
                    );
                }
            } else {
                if (this.resizeObserver !== null) {
                    this.resizeObserver.disconnect();
                    this.resizeObserver = null;

                    this.iframe.style.removeProperty("min-width");
                    this.iframe.style.removeProperty("min-height");
                }
            }
        }
    }

    createIframe(): HTMLIFrameElement {
        let iframe = document.createElement("iframe");

        let self = this;
        iframe.addEventListener("load", function () {
            // Careful, this code runs with a delay! If this iframe has
            // already been replaced by other content, do nothing.
            if (
                self.iframe !== iframe ||
                self.resizeObserver !== null ||
                !self.state.resize_to_fit_content
            ) {
                return;
            }

            self.resizeObserver = tryCreateIframeResizeObserver(iframe);
        });

        return iframe;
    }

    runScriptsInElement(): void {
        for (let oldScriptElement of this.element.querySelectorAll("script")) {
            // Create a new script element
            const newScriptElement = document.createElement("script");

            // Copy over all attributes
            for (let i = 0; i < oldScriptElement.attributes.length; i++) {
                const attr = oldScriptElement.attributes[i];
                newScriptElement.setAttribute(attr.name, attr.value);
            }

            // And the source itself
            newScriptElement.appendChild(
                document.createTextNode(oldScriptElement.innerHTML)
            );

            // Finally replace the old script element with the new one so
            // the browser executes it
            oldScriptElement.parentNode!.replaceChild(
                newScriptElement,
                oldScriptElement
            );
        }
    }
}

function isUrl(urlOrHtml: string): boolean {
    try {
        new URL(urlOrHtml);
        return true;
    } catch (error) {
        return false;
    }
}

function requiresIframe(html: string): boolean {
    return html.match(/^\s*(<!doctype |<html[ >])/i) !== null;
}

function tryCreateIframeResizeObserver(
    iframe: HTMLIFrameElement
): ResizeObserver | null {
    let contentDoc = iframe.contentDocument;
    if (contentDoc === null) {
        return null;
    }

    let docElement = contentDoc.documentElement;

    let resizeObserver = new ResizeObserver(function () {
        iframe.style.minWidth = `${docElement.scrollWidth}px`;
        iframe.style.minHeight = `${docElement.scrollHeight}px`;
    });
    resizeObserver.observe(docElement);

    return resizeObserver;
}
