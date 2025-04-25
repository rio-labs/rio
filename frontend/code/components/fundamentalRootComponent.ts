import { pixelsPerRem } from "../app";
import {
    componentsById,
    ComponentStatesUpdateContext,
} from "../componentManagement";
import { ComponentId } from "../dataModels";
import { Debouncer } from "../debouncer";
import { callRemoteMethodDiscardResponse } from "../rpc";
import { getAllocatedHeightInPx, getAllocatedWidthInPx } from "../utils";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";

let notifyBackendOfWindowSizeChange = new Debouncer({
    callback: (width: number, height: number) => {
        try {
            callRemoteMethodDiscardResponse("onWindowSizeChange", {
                new_width: width,
                new_height: height,
            });
        } catch (e) {
            console.warn(`Couldn't notify backend of window resize: ${e}`);
        }
    },
});

export type FundamentalRootComponentState = ComponentState & {
    _type_: "FundamentalRootComponent-builtin";
    content: ComponentId;
    connection_lost_component: ComponentId;
    dev_tools: ComponentId | null;
};

export class FundamentalRootComponent extends ComponentBase<FundamentalRootComponentState> {
    private userRootContainer: HTMLElement;
    public userOverlaysContainer: HTMLElement;

    private devToolsContainer: HTMLElement;
    public devToolsOverlaysContainer: HTMLElement;
    public devToolsHighlighterContainer: HTMLElement;

    private connectionLostPopupContainer: HTMLElement;
    public connectionLostPopupOverlaysContainer: HTMLElement;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-fundamental-root-component");

        element.innerHTML = `
            <div class="rio-user-root-container-outer">
                <div>
                    <div class="rio-user-root-container-inner"></div>
                </div>
            </div>
            <div class="rio-user-overlays-container"></div>
            <div class="rio-dev-tools-highlighter-container-outer">
                <div class="rio-dev-tools-highlighter-container-inner"></div>
            </div>
            <div class="rio-connection-lost-popup-container"></div>
            <div class="rio-connection-lost-popup-overlays-container"></div>
            <div class="rio-dev-tools-container"></div>
            <div class="rio-dev-tools-overlays-container"></div>
        `;

        this.userRootContainer = element.querySelector(
            ".rio-user-root-container-inner"
        ) as HTMLElement;
        this.userOverlaysContainer = element.querySelector(
            ".rio-user-overlays-container"
        ) as HTMLElement;

        this.devToolsContainer = element.querySelector(
            ".rio-dev-tools-container"
        ) as HTMLElement;
        this.devToolsOverlaysContainer = element.querySelector(
            ".rio-dev-tools-overlays-container"
        ) as HTMLElement;
        this.devToolsHighlighterContainer = element.querySelector(
            ".rio-dev-tools-highlighter-container-inner"
        ) as HTMLElement;

        this.connectionLostPopupContainer = element.querySelector(
            ".rio-connection-lost-popup-container"
        ) as HTMLElement;
        this.connectionLostPopupOverlaysContainer = element.querySelector(
            ".rio-connection-lost-popup-overlays-container"
        ) as HTMLElement;

        // Watch for window size changes. This differs between debug mode and
        // release mode. If the dev sidebar is visible, it must be subtracted
        // from the window size. Scrolling also works differently: In release
        // mode we let the browser scroll, but in debug mode we scroll only the
        // user content, and not the sidebar.
        //
        // In debug mode, we can simply attach a ResizeObserver to the element
        // that contains (and scrolls) the user content. But in release mode
        // that element doesn't scroll, so we must obtain the actual window
        // size.
        if (globalThis.RIO_DEBUG_MODE) {
            let outerUserRootContainer = element.querySelector(
                ".rio-user-root-container-outer"
            ) as HTMLElement;
            new ResizeObserver(() => {
                // Notify the backend of the new size
                notifyBackendOfWindowSizeChange.call(
                    getAllocatedWidthInPx(outerUserRootContainer) /
                        pixelsPerRem,
                    getAllocatedHeightInPx(outerUserRootContainer) /
                        pixelsPerRem
                );
            }).observe(outerUserRootContainer);
        } else {
            window.addEventListener("resize", () => {
                notifyBackendOfWindowSizeChange.call(
                    window.innerWidth / pixelsPerRem,
                    window.innerHeight / pixelsPerRem
                );
            });
        }

        // Since we don't have a parent component, we have to add ourselves to
        // the DOM
        //
        // It's important that this happens here, because some other code might
        // rely on some of these globals (like the overlay container) to be
        // accessible.
        document.body.appendChild(element);

        return element;
    }

    updateElement(
        deltaState: DeltaState<FundamentalRootComponentState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        // User components
        if (deltaState.content !== undefined) {
            this.replaceOnlyChild(
                context,
                deltaState.content,
                this.userRootContainer
            );
        }

        // Connection lost popup
        if (deltaState.connection_lost_component !== undefined) {
            this.replaceOnlyChild(
                context,
                deltaState.connection_lost_component,
                this.connectionLostPopupContainer
            );
        }

        // Dev tools sidebar
        if (deltaState.dev_tools !== undefined) {
            this.replaceOnlyChild(
                context,
                deltaState.dev_tools,
                this.devToolsContainer
            );

            if (deltaState.dev_tools !== null) {
                let devTools = componentsById[deltaState.dev_tools]!;
                devTools.element.classList.add("rio-dev-tools");
            }

            // Enable or disable the user content scroller depending on whether
            // there are dev-tools
            this.element.dataset.hasDevTools = `${
                deltaState.dev_tools !== null
            }`;
        }
    }
}
