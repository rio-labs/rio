import { componentsById } from '../componentManagement';
import { ComponentId } from '../dataModels';
import { setConnectionLostPopupVisibleUnlessGoingAway } from '../rpc';
import { ComponentBase, ComponentState } from './componentBase';

export type FundamentalRootComponentState = ComponentState & {
    _type_: 'FundamentalRootComponent-builtin';
    content: ComponentId;
    connection_lost_component: ComponentId;
    dev_tools: ComponentId | null;
};

export class FundamentalRootComponent extends ComponentBase {
    state: Required<FundamentalRootComponentState>;

    private userContentScroller = document.querySelector(
        '.rio-user-content-scroller'
    ) as HTMLElement;
    private userRootContainer = document.querySelector(
        '.rio-user-root-container'
    ) as HTMLElement;
    private connectionLostPopupContainer = document.querySelector(
        '.rio-connection-lost-popup-container'
    ) as HTMLElement;
    private devToolsContainer = document.querySelector(
        '.rio-dev-tools-container'
    ) as HTMLElement;

    createElement(): HTMLElement {
        return document.querySelector(
            '.rio-fundamental-root-component'
        ) as HTMLElement;
    }

    updateElement(
        deltaState: FundamentalRootComponentState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        // User components
        if (deltaState.content !== undefined) {
            this.replaceOnlyChild(
                latentComponents,
                deltaState.content,
                this.userRootContainer
            );
        }

        // Connection lost popup
        if (deltaState.connection_lost_component !== undefined) {
            let oldConnectionLostPopup =
                this.connectionLostPopupContainer.firstElementChild;
            let connectionLostPopupVisible =
                oldConnectionLostPopup === null
                    ? false // It's hidden by default
                    : oldConnectionLostPopup.classList.contains(
                          'rio-connection-lost-popup-visible'
                      );

            this.replaceOnlyChild(
                latentComponents,
                deltaState.connection_lost_component,
                this.connectionLostPopupContainer
            );

            let connectionLostPopupElement =
                this.connectionLostPopupContainer.firstElementChild!;
            connectionLostPopupElement.classList.add(
                'rio-connection-lost-popup'
            );

            // Looking up elements via selector is wonky if the element has only
            // just been added. Give the browser time to update.
            requestAnimationFrame(() =>
                setConnectionLostPopupVisibleUnlessGoingAway(
                    connectionLostPopupVisible
                )
            );
        }

        // Dev tools sidebar
        if (deltaState.dev_tools !== undefined) {
            this.replaceOnlyChild(
                latentComponents,
                deltaState.dev_tools,
                this.devToolsContainer
            );

            if (deltaState.dev_tools !== null) {
                let devTools = componentsById[deltaState.dev_tools]!;
                devTools.element.classList.add('rio-dev-tools');
            }

            // Enable or disable the user content scroller depending on whether
            // there are dev-tools
            this.userContentScroller.dataset.enabled = `${
                deltaState.dev_tools !== null
            }`;
        }
    }
}
