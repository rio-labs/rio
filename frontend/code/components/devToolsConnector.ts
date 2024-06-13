import { ComponentId } from '../dataModels';
import { LayoutContext } from '../layouting';
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

    // If layout display components exists, they register here
    public componentIdsToLayoutDisplays: Map<
        ComponentId,
        LayoutDisplayComponent
    > = new Map();

    createElement(): HTMLElement {
        // Make the component globally known
        globalThis.RIO_DEV_TOOLS = this;

        // Create the element
        let element = document.createElement('a');
        element.href = 'https://rio.dev?s=x0h';
        element.target = '_blank';
        element.classList.add('rio-dev-tools-connector');
        element.innerHTML = `
            <img src="/rio/assets/hosted/rio-logos/rio-logo-square.png">
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
    }): void {
        for (const [componentId, componentTree] of this
            .componentIdsToComponentTrees) {
            componentTree.afterComponentStateChange(deltaStates);
        }
    }

    /// Called when a re-layout was just performed. This allows the dev tools
    /// to update their display.
    public afterLayoutUpdate(): void {
        for (const [componentId, layoutDisplay] of this
            .componentIdsToLayoutDisplays) {
            layoutDisplay.afterLayoutUpdate();
        }
    }
}
