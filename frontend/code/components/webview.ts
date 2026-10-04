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
    private boundMessageHandler: ((event: MessageEvent) => void) | null = null;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-webview");

        this.boundMessageHandler = (event: MessageEvent) => {
            if (event.data?.type !== "rioWebviewMessage") return;

            if (this.iframe !== null) {
                if (event.source !== this.iframe.contentWindow) return;
            } else {
                if (event.data.webviewId !== this.id) return;
            }

            this.sendMessageToBackend(event.data.payload);
        };
        window.addEventListener("message", this.boundMessageHandler);

        return element;
    }

    onDestruction(): void {
        super.onDestruction();
        if (this.boundMessageHandler !== null) {
            window.removeEventListener("message", this.boundMessageHandler);
            this.boundMessageHandler = null;
        }
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
                    this.iframe.srcdoc = injectRioSendMessageForIframe(
                        deltaState.content
                    );

                    this.element.appendChild(this.iframe);
                } else {
                    // Clean up stuff we no longer need
                    this.iframe = null;
                    this.resizeObserver = null;

                    // Load the HTML
                    this.element.innerHTML = deltaState.content;

                    // Just setting the innerHTML doesn't run scripts. Do that
                    // manually.
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

            // Inject rioSendMessage for inline scripts. External scripts
            // (those with a `src` attribute) are not modified.
            //
            // The binding is wrapped in a block scope (`{ ... }`) with
            // `const`, so that each script gets its own Webview-scoped
            // `rioSendMessage`. A plain global `var` would be shared by all
            // inline Webviews on the page (last script to run wins), which
            // misroutes messages from deferred callbacks such as event
            // listeners, `IntersectionObserver`s or `setTimeout`s to the
            // wrong Webview.
            //
            // Side effects of the block scope (documented limitations):
            // - Top-level `let`/`const`/`class` declarations are no longer
            //   shared across `<script>` tags. (`var` and sloppy-mode
            //   function declarations still leak to the global scope.)
            // - A `'use strict'` directive is preserved (see below), but must
            //   appear as the first statement, optionally preceded by
            //   whitespace and `//`/`/* */` comments only.
            let content = oldScriptElement.innerHTML;
            if (!oldScriptElement.hasAttribute("src")) {
                // A `'use strict'` directive only applies to scripts and
                // functions, not bare blocks, so it would silently stop
                // working inside the block below. If the user code requests
                // strict mode, repeat the directive at the top of the script,
                // which makes the entire script (block included) strict.
                // `startsWithUseStrict` is intentionally conservative: it may
                // miss exotic prologues, but it can never report strict mode
                // for code that wasn't strict to begin with.
                let prefix = "";
                if (startsWithUseStrict(content)) {
                    prefix = `'use strict';`;
                }

                content =
                    prefix +
                    `{const rioSendMessage=function(payload){window.parent.postMessage({type:"rioWebviewMessage",webviewId:${this.id},payload:payload},"*")};` +
                    content +
                    `}`;
            }

            // And the source itself
            newScriptElement.appendChild(document.createTextNode(content));

            // Finally replace the old script element with the new one so
            // the browser executes it
            oldScriptElement.parentNode!.replaceChild(
                newScriptElement,
                oldScriptElement
            );
        }
    }
}

function injectRioSendMessageForIframe(html: string): string {
    const scriptTag =
        '<script>var rioSendMessage=function(payload){parent.postMessage({type:"rioWebviewMessage",payload:payload},"*")}</script>';

    const closeHeadMatch = html.match(/<\/head>/i);
    if (closeHeadMatch !== null) {
        const insertPos = closeHeadMatch.index!;
        return html.slice(0, insertPos) + scriptTag + html.slice(insertPos);
    }

    return scriptTag + html;
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

/// Returns true if `source` starts with a `'use strict'` directive, i.e. a
/// `'use strict'` (or `"use strict"`) string literal as the first statement,
/// optionally preceded by whitespace and `//` / `/* */` comments only.
///
/// This is intentionally conservative: only the first string literal is
/// considered (later prologue strings are ignored), and anything unexpected
/// yields `false`. A missed directive merely runs the script in sloppy mode
/// (status quo), while a false positive would wrongly strict-ify sloppy code
/// — so the function is designed to never produce one.
///
/// Note: Block comments need no escape handling — per the language spec a
/// `/*` comment always ends at the first `*/`, backslashes included.
function startsWithUseStrict(source: string): boolean {
    let pos = 0;

    // Skip whitespace and comments
    while (pos < source.length) {
        let char = source[pos];

        if (
            char === " " ||
            char === "\t" ||
            char === "\n" ||
            char === "\r" ||
            char === "\f" ||
            char === "\v" ||
            char === "\u00a0" ||
            char === "\ufeff"
        ) {
            pos++;
        } else if (source.startsWith("//", pos)) {
            let end = source.indexOf("\n", pos);
            if (end === -1) {
                return false;
            }
            pos = end + 1;
        } else if (source.startsWith("/*", pos)) {
            let end = source.indexOf("*/", pos + 2);
            if (end === -1) {
                return false;
            }
            pos = end + 2;
        } else {
            break;
        }
    }

    // Expect an exact 'use strict' / "use strict" literal
    if (
        !source.startsWith("'use strict'", pos) &&
        !source.startsWith('"use strict"', pos)
    ) {
        return false;
    }
    pos += "'use strict'".length;

    // The literal must form a complete statement: what follows must be
    // horizontal whitespace/comments and then `;`, a line terminator, or the
    // end of the source. (This excludes e.g. `'use strict' + x`, which is a
    // binary expression and hence not a directive.)
    while (pos < source.length) {
        let char = source[pos];

        if (
            char === " " ||
            char === "\t" ||
            char === "\u00a0" ||
            char === "\ufeff"
        ) {
            pos++;
        } else if (source.startsWith("//", pos)) {
            let end = source.indexOf("\n", pos);
            if (end === -1) {
                return false;
            }
            pos = end + 1;
        } else if (source.startsWith("/*", pos)) {
            let end = source.indexOf("*/", pos + 2);
            if (end === -1) {
                return false;
            }
            pos = end + 2;
        } else {
            break;
        }
    }

    return (
        pos >= source.length ||
        source[pos] === ";" ||
        source[pos] === "\n" ||
        source[pos] === "\r"
    );
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
