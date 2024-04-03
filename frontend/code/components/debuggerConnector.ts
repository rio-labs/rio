import { LayoutContext } from '../layouting';
import { ComponentBase, ComponentState } from './componentBase';
import { ComponentTreeComponent } from './componentTree';

export type DebuggerConnectorState = ComponentState & {
    _type_: 'DebuggerConnector-builtin';
};

export class DebuggerConnectorComponent extends ComponentBase {
    state: Required<DebuggerConnectorState>;

    // If a component tree page is currently visible it is stored here
    public componentTree: ComponentTreeComponent | null = null;

    createElement(): HTMLElement {
        // Make the component globally known
        globalThis.RIO_DEBUGGER = this;

        // Create the element
        let element = document.createElement('a');
        element.href = 'https://rio.dev';
        element.target = '_blank';
        element.classList.add('rio-debugger-navigation-rio-logo');
        element.innerHTML = `
            <img src="/rio/asset/rio-logos/rio-logo-square.png">
            <div>Rio</div>
        `;
        return element;
    }

    updateElement(
        deltaState: DebuggerConnectorState,
        latentComponents: Set<ComponentBase>
    ): void {}

    updateNaturalWidth(ctx: LayoutContext): void {
        this.naturalWidth = 3;
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        this.naturalHeight = 7;
    }

    /// Called when the state of any component changes. This allows the debugger
    /// to update its display.
    public afterComponentStateChange(deltaStates: {
        [key: string]: { [key: string]: any };
    }) {
        // Pass on the message if a component tree is visible
        if (this.componentTree !== null) {
            this.componentTree.afterComponentStateChange(deltaStates);
        }
    }
}
