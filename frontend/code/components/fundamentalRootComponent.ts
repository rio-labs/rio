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

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-fundamental-root-component');

        return element;
    }

    updateElement(
        deltaState: FundamentalRootComponentState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

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
    }
}
