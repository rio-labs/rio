import { setDevToolsConnector } from "../app";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { ComponentTreeComponent } from "./componentTree";

export type DevToolsConnectorState = ComponentState & {
    _type_: "DevToolsConnector-builtin";
};

export class DevToolsConnectorComponent extends ComponentBase<DevToolsConnectorState> {
    // If component tree components exists, they register here
    public componentTreeComponent: ComponentTreeComponent | null = null;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        // Make the component globally known
        setDevToolsConnector(this);

        // Create the element
        let element = document.createElement("a");
        element.href = "https://rio.dev?s=x0h";
        element.target = "_blank";
        element.classList.add("rio-dev-tools-connector");
        element.innerHTML = `
            <img src="${globalThis.RIO_BASE_URL}rio/assets/hosted/rio_logos/rio_logo_square.png">
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
        if (this.componentTreeComponent !== null) {
            this.componentTreeComponent.afterComponentStateChange(deltaStates);
        }
    }

    /// Lets the user select a component in the `ComponentTree` by clicking on
    /// it in the DOM.
    public async pickComponent(): Promise<void> {
        console.assert(
            this.componentTreeComponent !== null,
            `There is no ComponentTreeComponent registered?!`
        );

        await this.componentTreeComponent!.pickComponent();
    }
}
