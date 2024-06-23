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

    public overlaysContainer: HTMLElement;

    private userRootContainer: HTMLElement;
    private connectionLostPopupContainer: HTMLElement;
    private devToolsContainer: HTMLElement;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-fundamental-root-component');

        element.innerHTML = `
            <div class="rio-user-root-container-outer">
                <div class="rio-user-root-container-inner"></div>
            </div>
            <div class="rio-overlays-container"></div>
            <div class="rio-connection-lost-popup-container"></div>
            <div class="rio-dev-tools-container"></div>
        `;

        this.overlaysContainer = element.querySelector(
            '.rio-overlays-container'
        ) as HTMLElement;

        this.userRootContainer = element.querySelector(
            '.rio-user-root-container-inner'
        ) as HTMLElement;
        this.connectionLostPopupContainer = element.querySelector(
            '.rio-connection-lost-popup-container'
        ) as HTMLElement;
        this.devToolsContainer = element.querySelector(
            '.rio-dev-tools-container'
        ) as HTMLElement;

        return element;
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
            this.replaceOnlyChild(
                latentComponents,
                deltaState.connection_lost_component,
                this.connectionLostPopupContainer
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
            this.element.dataset.hasDevTools = `${
                deltaState.dev_tools !== null
            }`;
        }
    }
}
