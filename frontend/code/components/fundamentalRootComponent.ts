import { pixelsPerRem } from '../app';
import { componentsById } from '../componentManagement';
import { LayoutContext } from '../layouting';
import { ComponentId } from '../dataModels';
import { setConnectionLostPopupVisibleUnlessGoingAway } from '../rpc';
import { ComponentBase, ComponentState } from './componentBase';

export type FundamentalRootComponentState = ComponentState & {
    _type_: 'FundamentalRootComponent-builtin';
    content: ComponentId;
    debugger: ComponentId | null;
    connection_lost_component: ComponentId;
};

export class FundamentalRootComponent extends ComponentBase {
    state: Required<FundamentalRootComponentState>;

    // The width and height for any components that want to span the entire
    // screen and not scroll. This differs from just the window width/height,
    // because the debugger can also take up space and doesn't count as part of
    // the user's app.
    public overlayWidth: number = 0;
    public overlayHeight: number = 0;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-fundamental-root-component');
        return element;
    }

    updateElement(
        deltaState: FundamentalRootComponentState,
        latentComponents: Set<ComponentBase>
    ): void {
        // Update the children
        let content = deltaState.content ?? this.state.content;
        let connectionLostComponent =
            deltaState.connection_lost_component ??
            this.state.connection_lost_component;
        let debugger_ = deltaState.debugger ?? this.state.debugger;

        let children = [content, connectionLostComponent];
        if (debugger_ !== null) {
            children.push(debugger_);
        }

        this.replaceChildren(latentComponents, children);

        // Initialize CSS
        let oldConnectionLostPopup = document.querySelector(
            '.rio-connection-lost-popup'
        );
        let connectionLostPopupVisible =
            oldConnectionLostPopup === null
                ? false // It's hidden by default
                : oldConnectionLostPopup.classList.contains(
                      'rio-connection-lost-popup-visible'
                  );

        let connectionLostPopupElement = this.element
            .children[1] as HTMLElement;
        connectionLostPopupElement.classList.add('rio-connection-lost-popup');

        if (deltaState.debugger !== null) {
            let debuggerElement = this.element.children[2] as HTMLElement;
            debuggerElement.classList.add('rio-debugger');
        }

        // Looking up elements via selector is wonky if the element has only
        // just been added. Give the browser time to update.
        setTimeout(
            () =>
                setConnectionLostPopupVisibleUnlessGoingAway(
                    connectionLostPopupVisible
                ),
            0
        );

        this.makeLayoutDirty();
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        // Don't use `window.innerWidth`. It appears to be rounded to the
        // nearest integer, so it's inaccurate.
        //
        // `getBoundingClientRect()` doesn't account for scroll bars, but our
        // <html> element is set to `overflow: hidden` anyway, so that's not an issue.
        let rect = document.documentElement.getBoundingClientRect();
        this.naturalWidth = this.allocatedWidth = rect.width / pixelsPerRem;
        this.naturalHeight = this.allocatedHeight = rect.height / pixelsPerRem;
    }

    updateAllocatedWidth(ctx: LayoutContext): void {
        // Overlays take up the full window
        this.overlayWidth = this.allocatedWidth;

        // If there's a debugger, account for that
        if (this.state.debugger !== null) {
            let dbg = componentsById[this.state.debugger]!;
            dbg.allocatedWidth = dbg.requestedWidth;
            this.overlayWidth -= dbg.allocatedWidth;
        }

        // The child receives the remaining width. (The child is a
        // ScrollContainer, it takes care of scrolling if the user content is
        // too large)
        let child = componentsById[this.state.content]!;
        child.allocatedWidth = this.overlayWidth;

        // Despite being an overlay, the connection lost popup should also cover
        // the debugger
        let connectionLostPopup =
            componentsById[this.state.connection_lost_component]!;
        connectionLostPopup.allocatedWidth = this.allocatedWidth;
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        // Already done in updateNaturalWidth
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        // Overlays take up the full window
        this.overlayHeight = this.allocatedHeight;

        // If there's a debugger, set its height and position it
        if (this.state.debugger !== null) {
            let dbgInst = componentsById[this.state.debugger]!;
            dbgInst.allocatedHeight = this.overlayHeight;

            // Position it
            let dbgElement = dbgInst.element;
            dbgElement.style.left = `${this.overlayWidth}rem`;
            dbgElement.style.top = '0';
        }

        // The connection lost popup is an overlay
        let connectionLostPopup =
            componentsById[this.state.connection_lost_component]!;
        connectionLostPopup.allocatedHeight = this.overlayHeight;

        // The child once again receives the remaining width. (The child is a
        // ScrollContainer, it takes care of scrolling if the user content is
        // too large)
        let child = componentsById[this.state.content]!;
        child.allocatedHeight = this.overlayHeight;
    }
}
