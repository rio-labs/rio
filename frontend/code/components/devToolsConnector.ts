import { LayoutContext } from '../layouting';
import { ComponentBase, ComponentState } from './componentBase';
import { ComponentTreeComponent } from './componentTree';

export type DevToolsConnectorState = ComponentState & {
    _type_: 'DevToolsConnector-builtin';
};

export class DevToolsConnectorComponent extends ComponentBase {
    state: Required<DevToolsConnectorState>;

    // If a component tree page is currently visible it is stored here
    public componentTree: ComponentTreeComponent | null = null;

    createElement(): HTMLElement {
        // Make the component globally known
        globalThis.RIO_DEV_TOOLS = this;

        // Create the element
        let element = document.createElement('a');
        element.href = 'https://rio.dev';
        element.target = '_blank';
        element.classList.add('rio-dev-tools-connector');
        element.innerHTML = `
            <img src="/rio/asset/rio-logos/rio-logo-square.png">
            <div style="font-size: 1.2rem">Rio</div>
            <!-- <div style="font-size: 0.9rem">Dev Tools</div> -->
        `;
        return element;
    }

    updateElement(
        deltaState: DevToolsConnectorState,
        latentComponents: Set<ComponentBase>
    ): void {}

    updateNaturalWidth(ctx: LayoutContext): void {
        this.naturalWidth = 3;
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        this.naturalHeight = 7;
    }

    /// Called when the state of any component changes. This allows the dev
    /// tools to update their display.
    public afterComponentStateChange(deltaStates: {
        [key: string]: { [key: string]: any };
    }) {
        // Pass on the message if a component tree is visible
        if (this.componentTree !== null) {
            this.componentTree.afterComponentStateChange(deltaStates);
        }
    }
}
