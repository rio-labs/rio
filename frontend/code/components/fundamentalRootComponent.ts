import { pixelsPerRem } from '../app';
import { componentsById } from '../componentManagement';
import { LayoutContext } from '../layouting';
import { ComponentId } from '../dataModels';
import { setConnectionLostPopupVisibleUnlessGoingAway } from '../rpc';
import { ComponentBase, ComponentState } from './componentBase';

export type FundamentalRootComponentState = ComponentState & {
    _type_: 'FundamentalRootComponent-builtin';
    content: ComponentId;
    dev_tools: ComponentId | null;
    connection_lost_component: ComponentId;
};

export class FundamentalRootComponent extends ComponentBase {
    state: Required<FundamentalRootComponentState>;

    // The width and height for any components that want to span the entire
    // screen and not scroll. This differs from just the window width/height,
    // because the dev tools can also take up space and doesn't count as part of
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
        let devTools = deltaState.dev_tools ?? this.state.dev_tools;

        let children = [content, connectionLostComponent];
        if (devTools !== null) {
            children.push(devTools);
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

        if (deltaState.dev_tools !== null) {
            let devToolsElement = this.element.children[2] as HTMLElement;
            devToolsElement.classList.add('rio-dev-tools');
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
        // <html> element is set to `overflow: hidden` anyway, so that's not an
        // issue.
        let rect = document.documentElement.getBoundingClientRect();
        this.naturalWidth = this.allocatedWidth = rect.width / pixelsPerRem;
        this.naturalHeight = this.allocatedHeight = rect.height / pixelsPerRem;
    }

    updateAllocatedWidth(ctx: LayoutContext): void {
        // Overlays take up the full window
        this.overlayWidth = this.allocatedWidth;

        // If the dev tools are visible, account for that
        if (this.state.dev_tools !== null) {
            let devToolsComponent = componentsById[this.state.dev_tools]!;
            devToolsComponent.allocatedWidth = devToolsComponent.requestedWidth;

            // Even if dev tools are provided, only display them if the screen
            // is wide enough. Having them show up on a tall mobile screen is
            // very awkward.
            //
            // Since the allocated height isn't available here yet, use the
            // window size instead.
            let screenWidth = window.innerWidth / pixelsPerRem;
            let screenHeight = window.innerHeight / pixelsPerRem;

            if (screenWidth > 50 && screenHeight > 30) {
                devToolsComponent.element.style.removeProperty('display');
                this.element.classList.remove('rio-dev-tools-hidden');
                this.overlayWidth -= devToolsComponent.allocatedWidth;
            } else {
                devToolsComponent.element.style.display = 'none';
                this.element.classList.add('rio-dev-tools-hidden');
            }
        }

        // The child receives the remaining width. (The child is a
        // ScrollContainer, it takes care of scrolling if the user content is
        // too large)
        let child = componentsById[this.state.content]!;
        child.allocatedWidth = this.overlayWidth;

        // Despite being an overlay, the connection lost popup should also cover
        // the dev tools
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

        // If dev tools are present, set their height and position it
        if (this.state.dev_tools !== null) {
            let dbgInst = componentsById[this.state.dev_tools]!;
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
