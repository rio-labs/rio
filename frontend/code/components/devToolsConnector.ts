import { setDevToolsConnector } from '../app';
import { ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';
import { ComponentTreeComponent } from './componentTree';
import { LayoutDisplayComponent } from './layoutDisplay';

export type DevToolsConnectorState = ComponentState & {
    _type_: 'DevToolsConnector-builtin';
};

export class DevToolsConnectorComponent extends ComponentBase {
    state: Required<DevToolsConnectorState>;

    // If component tree components exists, they register here
    public componentIdsToComponentTrees: Map<
        ComponentId,
        ComponentTreeComponent
    > = new Map();

    createElement(): HTMLElement {
        // Make the component globally known
        setDevToolsConnector(this);

        // Create the element
        let element = document.createElement('a');
        element.href = 'https://rio.dev?s=x0h';
        element.target = '_blank';
        element.classList.add('rio-dev-tools-connector');
        element.innerHTML = `
            <img src="/rio/assets/hosted/rio_logos/rio_logo_square.png">
            <div style="font-size: 1.2rem">Rio</div>
            <!-- <div style="font-size: 0.9rem">Dev Tools</div> -->
        `;
        return element;
    }

    /// Called when the state of any component changes. This allows the dev
    /// tools to update their display.
    public afterComponentStateChange(deltaStates: {
        [key: string]: { [key: string]: any };
    }): void {
        for (const [componentId, componentTree] of this
            .componentIdsToComponentTrees) {
            componentTree.afterComponentStateChange(deltaStates);
        }
    }

    /// Lets the user select a component in the `ComponentTree` by clicking on
    /// it in the DOM.
    public async pickComponent(): Promise<void> {
        console.assert(this.componentIdsToComponentTrees.size === 1);
        let [componentTree] = this.componentIdsToComponentTrees.values();

        await componentTree.pickComponent();
    }
}
