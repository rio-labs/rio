import { componentsById, getRootScroller } from '../componentManagement';
import { applyIcon } from '../designApplication';
import { ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';
import { DevToolsConnectorComponent } from './devToolsConnector';
import { Highlighter } from '../highlighter';
import {
    getDisplayableChildren,
    getDisplayedRootComponent,
} from '../devToolsTreeWalk';

export type ComponentTreeState = ComponentState & {
    _type_: 'ComponentTree-builtin';
    component_id?: number;
};

export class ComponentTreeComponent extends ComponentBase {
    state: Required<ComponentTreeState>;

    private highlighter: Highlighter;

    private nodesByComponent: WeakMap<ComponentBase, HTMLElement> =
        new WeakMap();

    // FIXME: Dead entries are never removed from `nodesByComponentId`

    createElement(): HTMLElement {
        // Register this component with the global dev tools component, so it
        // receives updates when a component's state changes.
        let devTools: DevToolsConnectorComponent = globalThis.RIO_DEV_TOOLS;
        console.assert(devTools !== null);
        devTools.componentIdsToComponentTrees.set(this.id, this);

        // Spawn the HTML
        let element = document.createElement('div');
        element.classList.add('rio-dev-tools-component-tree');

        // Create the highlighter
        this.highlighter = new Highlighter();

        // Populate. This needs to lookup the root component, which isn't in the
        // tree yet.
        setTimeout(() => {
            this.buildTree();
        }, 0);

        return element;
    }

    onDestruction(): void {
        // Unregister this component from the global dev tools component
        let devTools: DevToolsConnectorComponent = globalThis.RIO_DEV_TOOLS;
        console.assert(devTools !== null);
        devTools.componentIdsToComponentTrees.delete(this.id);

        // Destroy the highlighter
        this.highlighter.destroy();
    }

    updateElement(
        deltaState: ComponentTreeState,
        latentComponents: Set<ComponentBase>
    ): void {
        console.debug('TREE', deltaState);

        if (deltaState.component_id !== undefined) {
            // Highlight the tree item
            //
            // This might have to lookup other components. Let the state update
            // finish first.
            setTimeout(() => {
                this.highlightSelectedComponent();
            }, 0);
        }
    }

    /// Returns the currently selected component. This will impute a sensible
    /// default if the selected component no longer exists.
    getSelectedComponent(): ComponentBase {
        // Does the previously selected component still exist?
        let selectedComponent: ComponentBase | undefined =
            componentsById[this.state.component_id];

        if (selectedComponent !== undefined) {
            return selectedComponent;
        }

        // Default to the root component
        let result = getDisplayedRootComponent();

        this.setStateAndNotifyBackend({
            component_id: result.id,
        });

        return result;
    }

    buildTree(): void {
        // Get the rootmost displayed component
        let rootComponent = getDisplayedRootComponent();

        // Build a node for it
        this.element.appendChild(this.getNodeFor(rootComponent));

        // Attempting to immediately access the just spawned items fails,
        // apparently because the browser needs to get control first. Any
        // further actions will happen with a delay.
        setTimeout(() => {
            // Don't start off with a fully collapsed tree
            if (!this.getNodeExpanded(rootComponent)) {
                this.setNodeExpanded(rootComponent, true);
            }

            // Highlight the selected component
            this.highlightSelectedComponent();
        }, 0);
    }

    getNodeFor(component: ComponentBase): HTMLElement {
        let node = this.nodesByComponent.get(component);
        if (node !== undefined) {
            return node;
        }

        node = this.buildNode(component);
        this.nodesByComponent.set(component, node);
        return node;
    }

    buildNode(component: ComponentBase): HTMLElement {
        // Create the element for this item
        let node = document.createElement('div');
        node.id = `rio-dev-tools-component-tree-item-${component.id}`;
        node.classList.add('rio-dev-tools-component-tree-item');

        // Create the header
        let children = getDisplayableChildren(component);
        let header = document.createElement('div');
        header.classList.add('rio-dev-tools-component-tree-item-header');
        header.textContent = component.state._python_type_;

        // Expander arrow, or at least a placeholder for it
        let iconElement = document.createElement('div');
        iconElement.style.display = 'flex'; // Centers the SVG vertically
        header.insertBefore(iconElement, header.firstChild);

        if (children.length > 0) {
            applyIcon(
                iconElement,
                'material/keyboard-arrow-right',
                'currentColor'
            );
        }

        node.appendChild(header);

        // Add the children
        let childrenContainer = document.createElement('div');
        childrenContainer.classList.add(
            'rio-dev-tools-component-tree-item-children'
        );
        node.appendChild(childrenContainer);

        for (let childInfo of children) {
            childrenContainer.appendChild(this.getNodeFor(childInfo));
        }

        // Expand the node, or not
        let expanded = this.getNodeExpanded(component);
        node.dataset.expanded = `${expanded}`;
        node.dataset.hasChildren = `${children.length > 0}`;

        // Add icons to give additional information
        let icons: string[] = [];

        // Icon: Container
        if (children.length <= 1) {
        } else if (children.length > 9) {
            icons.push('material/filter-9-plus');
        } else {
            icons.push(`material/filter-${children.length}`);
        }

        // Icon: Key
        if (component.state._key_ !== null) {
            icons.push('material/key');
        }

        let spacer = document.createElement('div');
        spacer.style.flexGrow = '1';
        header.appendChild(spacer);

        for (let icon of icons) {
            let iconElement = document.createElement('div');
            iconElement.style.display = 'flex'; // Centers the SVG vertically
            header.appendChild(iconElement);
            applyIcon(iconElement, icon, 'currentColor');
        }

        // Click...
        header.addEventListener('click', (event) => {
            event.stopPropagation();

            // Select the component
            this.setStateAndNotifyBackend({
                component_id: component.id,
            });

            // Highlight the tree item
            this.highlightSelectedComponent();

            // Expand / collapse the node's children
            let expanded = this.getNodeExpanded(component);
            this.setNodeExpanded(component, !expanded);

            // Scroll to the element
            let componentElement = component.element;
            componentElement.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest',
                inline: 'nearest',
            });
        });

        // Highlight the actual component when the element is hovered
        header.addEventListener('mouseover', (event) => {
            this.highlighter.moveTo(component.element);
            event.stopPropagation();
        });

        // Remove any highlighters when the element is unhovered
        node.addEventListener('mouseout', (event) => {
            this.highlighter.moveTo(null);
            event.stopPropagation();
        });

        return node;
    }

    getNodeExpanded(instance: ComponentBase): boolean {
        // This is monkey-patched directly in the instance to preserve it across
        // dev-tools rebuilds.

        // @ts-ignore
        return instance._rio_dev_tools_tree_expanded_ === true;
    }

    setNodeExpanded(
        component: ComponentBase,
        expanded: boolean,
        allowRecursion: boolean = true
    ) {
        // Monkey-patch the new value in the instance
        // @ts-ignore
        component._rio_dev_tools_tree_expanded_ = expanded;

        // Get the node element for this instance
        let element = document.getElementById(
            `rio-dev-tools-component-tree-item-${component.id}`
        );

        // Expand / collapse its children.
        //
        // Only do so if there are children, as the additional empty spacing
        // looks dumb otherwise.
        let children = getDisplayableChildren(component);

        if (element !== null) {
            element.dataset.expanded = `${expanded}`;
        }

        // If expanding, and the node only has a single child, expand that child
        // as well
        if (allowRecursion && expanded) {
            if (children.length === 1) {
                this.setNodeExpanded(children[0], true);
            }
        }
    }

    highlightSelectedComponent() {
        // Unhighlight all previously highlighted items
        for (let element of Array.from(
            document.querySelectorAll(
                '.rio-dev-tools-component-tree-item-header-weakly-selected, .rio-dev-tools-component-tree-item-header-strongly-selected'
            )
        )) {
            element.classList.remove(
                'rio-dev-tools-component-tree-item-header-weakly-selected',
                'rio-dev-tools-component-tree-item-header-strongly-selected'
            );
        }

        // Get the selected component
        let selectedComponent = this.getSelectedComponent();

        // Find all tree items
        let treeItems: HTMLElement[] = [];

        let cur: HTMLElement | null = document.getElementById(
            `rio-dev-tools-component-tree-item-${selectedComponent.id}`
        ) as HTMLElement;

        while (
            cur !== null &&
            cur.classList.contains('rio-dev-tools-component-tree-item')
        ) {
            treeItems.push(cur.firstElementChild as HTMLElement);
            cur = cur.parentElement!.parentElement;
        }

        // Strongly select the leafmost item
        treeItems[0].classList.add(
            'rio-dev-tools-component-tree-item-header-strongly-selected'
        );

        // Weakly select the rest
        for (let i = 1; i < treeItems.length; i++) {
            treeItems[i].classList.add(
                'rio-dev-tools-component-tree-item-header-weakly-selected'
            );
        }
    }

    nodeNeedsRebuild(
        component: ComponentBase,
        deltaState: ComponentState
    ): boolean {
        if ('key' in deltaState) {
            return true;
        }

        let propertyNamesWithChildren: string[] =
            globalThis.CHILD_ATTRIBUTE_NAMES[component.state['_type_']!] || [];

        for (let propertyName of propertyNamesWithChildren) {
            if (propertyName in deltaState) {
                return true;
            }
        }

        return false;
    }

    rebuildNode(node: HTMLElement, component: ComponentBase): void {
        let newNode = this.buildNode(component);
        this.nodesByComponent.set(component, newNode);

        node.parentElement!.insertBefore(newNode, node);
        node.remove();
    }

    /// Called by the global dev tools component when a component's state
    /// changes.
    public afterComponentStateChange(deltaStates: {
        [componentId: string]: { [key: string]: any };
    }) {
        // Look for components whose children have changed and rebuild their
        // nodes
        for (let [componentIdString, deltaState] of Object.entries(
            deltaStates
        )) {
            let component = componentsById[componentIdString]!;

            // If we haven't created a node for this component yet, there's no
            // need to update it
            let node = this.nodesByComponent.get(component);
            if (node === undefined) {
                continue;
            }

            if (this.nodeNeedsRebuild(component, deltaState)) {
                this.rebuildNode(node, component);
            }
        }

        // The component tree has been modified. Browsers struggle to retrieve
        // the new elements immediately, so wait a bit.
        setTimeout(() => {
            // Flash all changed components
            for (let componentId in deltaStates) {
                // Get the element. Not everything will show up, since some
                // components aren't displayed in the tree (internals).
                let element = document.getElementById(
                    `rio-dev-tools-component-tree-item-rio-id-${componentId}`
                );

                if (element === null) {
                    continue;
                }

                let elementHeader = element.firstElementChild as HTMLElement;

                // Flash the font to indicate a change
                elementHeader.classList.add(
                    'rio-dev-tools-component-tree-flash'
                );

                setTimeout(() => {
                    elementHeader.classList.remove(
                        'rio-dev-tools-component-tree-flash'
                    );
                }, 5000);
            }
        }, 0);
    }
}
