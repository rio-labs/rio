import { componentsById, getRootScroller } from '../componentManagement';
import { applyIcon } from '../designApplication';
import { ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';
import { DebuggerConnectorComponent } from './debuggerConnector';

export type ComponentTreeState = ComponentState & {
    _type_: 'ComponentTree-builtin';
};

export class ComponentTreeComponent extends ComponentBase {
    state: Required<ComponentTreeState>;

    /// When a component should be highlighted to the user, this HTML element
    /// does the highlighting.
    private highlighterElement: HTMLElement;

    private selectedComponentId: ComponentId | null = null;

    createElement(): HTMLElement {
        // Register this component with the global debugger, so it receives
        // updates when a component's state changes.
        let dbg: DebuggerConnectorComponent = globalThis.RIO_DEBUGGER;
        console.assert(dbg !== null);
        dbg.componentTree = this;

        // Spawn the HTML
        let element = document.createElement('div');
        element.classList.add('rio-debugger-tree-component-tree');

        // Populate. This needs to lookup the root component, which isn't in the
        // tree yet.
        requestAnimationFrame(() => {
            this.buildTree();
        });

        // Add the highlighter and hide it
        this.highlighterElement = document.createElement('div');
        this.highlighterElement.classList.add(
            'rio-debugger-component-highlighter'
        );
        document.body.appendChild(this.highlighterElement);

        this.moveHighlighterTo(null);

        return element;
    }

    onDestruction(): void {
        // Unregister this component from the global debugger
        let dbg: DebuggerConnectorComponent = globalThis.RIO_DEBUGGER;
        console.assert(dbg !== null);
        dbg.componentTree = null;

        // Remove any highlighters
        this.highlighterElement.remove();
    }

    updateElement(
        deltaState: ComponentState,
        latentComponents: Set<ComponentBase>
    ): void {}

    /// Returns the currently selected component. This will impute a sensible
    /// default if the selected component no longer exists.
    getSelectedComponent(): ComponentBase {
        // Does the previously selected component still exist?
        let selectedComponent: ComponentBase | undefined =
            this.selectedComponentId === null
                ? undefined
                : componentsById[this.selectedComponentId];

        if (selectedComponent !== undefined) {
            return selectedComponent;
        }

        // Default to the root
        let result = this.getDisplayedRootComponent();
        this.setSelectedComponent(result);
        return result;
    }

    /// Stores the currently selected component, without updating any UI. Also
    /// notifies the backend.
    setSelectedComponent(component: ComponentBase) {
        this.selectedComponentId = component.id;

        this.sendMessageToBackend({
            selectedComponentId: this.selectedComponentId,
        });
    }

    /// Many of the spawned components are internal to Rio and shouldn't be
    /// displayed to the user. This function makes that determination.
    shouldDisplayComponent(comp: ComponentBase): boolean {
        return !comp.state._rio_internal_;
    }

    _drillDown(comp: ComponentBase): ComponentBase[] {
        // Is this component displayable?
        if (this.shouldDisplayComponent(comp)) {
            return [comp];
        }

        // No, drill down
        let result: ComponentBase[] = [];

        for (let child of comp.children) {
            result.push(...this._drillDown(child));
        }

        return result;
    }

    /// Given a component, return all of its children which should be displayed
    /// in the tree.
    getDisplayableChildren(comp: ComponentBase): ComponentBase[] {
        let result: ComponentBase[] = [];

        // Keep drilling down until a component which should be displayed
        // is encountered
        for (let child of comp.children) {
            result.push(...this._drillDown(child));
        }

        return result;
    }

    /// Return the root component, but take care to discard any rio internal
    /// components.
    getDisplayedRootComponent(): ComponentBase {
        let rootScroller = getRootScroller();
        let userRoot = componentsById[rootScroller.state.content]!;
        return userRoot;
    }

    buildTree(): void {
        // Get the rootmost displayed component
        let rootComponent = this.getDisplayedRootComponent();

        // Clear the tree
        let element = this.element;
        element.innerHTML = '';

        // Build a fresh one
        this.buildNode(element, rootComponent, 0);

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

    buildNode(
        parentElement: HTMLElement,
        component: ComponentBase,
        level: number
    ) {
        // Create the element for this item
        let element = document.createElement('div');
        element.id = `rio-debugger-component-tree-item-${component.id}`;
        element.classList.add('rio-debugger-component-tree-item');
        parentElement.appendChild(element);

        // Create the header
        let children = this.getDisplayableChildren(component);
        let header = document.createElement('div');
        header.classList.add('rio-debugger-component-tree-item-header');
        header.textContent = component.state._python_type_;

        let iconElement = document.createElement('div');
        header.insertBefore(iconElement, header.firstChild);

        if (children.length > 0) {
            applyIcon(
                iconElement,
                'material/keyboard-arrow-right',
                'currentColor'
            );
        }

        element.appendChild(header);

        // Add the children
        let childElement = document.createElement('div');
        childElement.classList.add('rio-debugger-component-tree-item-children');
        element.appendChild(childElement);

        for (let childInfo of children) {
            this.buildNode(childElement, childInfo, level + 1);
        }

        // Expand the node, or not
        let expanded = this.getNodeExpanded(component);
        element.dataset.expanded = `${expanded}`;
        element.dataset.hasChildren = `${children.length > 0}`;

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
            header.appendChild(iconElement);
            applyIcon(iconElement, icon, 'currentColor');
        }

        // Click...
        header.addEventListener('click', (event) => {
            event.stopPropagation();

            // Select the component
            this.setSelectedComponent(component);

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
            this.moveHighlighterTo(component);
            event.stopPropagation();
        });

        // Remove any highlighters when the element is unhovered
        element.addEventListener('mouseout', (event) => {
            this.moveHighlighterTo(null);
            event.stopPropagation();
        });
    }

    /// Transition the highlighter to the given component. If the component is
    /// `null`, transition it out.
    moveHighlighterTo(component: ComponentBase | null) {
        // If no component is to be highlighted, make the highlighter the size
        // of the window, effectively hiding it. Overshoot by a bit to make sure
        // the highlighter's pulse animation doesn't make it visible by
        // accident.
        let left, top, width, height;

        if (component === null) {
            left = -10;
            top = -10;
            width = window.innerWidth + 20;
            height = window.innerHeight + 20;
        } else {
            let componentElement = component.element;
            let rect = componentElement.getBoundingClientRect();
            left = rect.left;
            top = rect.top;
            width = rect.width;
            height = rect.height;
        }

        // Move the highlighter
        this.highlighterElement.style.top = `${top}px`;
        this.highlighterElement.style.left = `${left}px`;
        this.highlighterElement.style.width = `${width}px`;
        this.highlighterElement.style.height = `${height}px`;
    }

    getNodeExpanded(instance: ComponentBase): boolean {
        // This is monkey-patched directly in the instance to preserve it across
        // debugger rebuilds.

        // @ts-ignore
        return instance._rio_debugger_expanded_ === true;
    }

    setNodeExpanded(
        component: ComponentBase,
        expanded: boolean,
        allowRecursion: boolean = true
    ) {
        // Monkey-patch the new value in the instance
        // @ts-ignore
        component._rio_debugger_expanded_ = expanded;

        // Get the node element for this instance
        let element = document.getElementById(
            `rio-debugger-component-tree-item-${component.id}`
        );

        // Expand / collapse its children.
        //
        // Only do so if there are children, as the additional empty spacing
        // looks dumb otherwise.
        let children = this.getDisplayableChildren(component);

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
                '.rio-debugger-component-tree-item-header-weakly-selected, .rio-debugger-component-tree-item-header-strongly-selected'
            )
        )) {
            element.classList.remove(
                'rio-debugger-component-tree-item-header-weakly-selected',
                'rio-debugger-component-tree-item-header-strongly-selected'
            );
        }

        // Get the selected component
        let selectedComponent = this.getSelectedComponent();

        // Find all tree items
        let treeItems: HTMLElement[] = [];

        let cur: HTMLElement | null = document.getElementById(
            `rio-debugger-component-tree-item-${selectedComponent.id}`
        ) as HTMLElement;

        while (
            cur !== null &&
            cur.classList.contains('rio-debugger-component-tree-item')
        ) {
            treeItems.push(cur.firstElementChild as HTMLElement);
            cur = cur.parentElement!.parentElement;
        }

        // Strongly select the leafmost item
        treeItems[0].classList.add(
            'rio-debugger-component-tree-item-header-strongly-selected'
        );

        // Weakly select the rest
        for (let i = 1; i < treeItems.length; i++) {
            treeItems[i].classList.add(
                'rio-debugger-component-tree-item-header-weakly-selected'
            );
        }
    }

    public afterComponentStateChange(deltaStates: {
        [key: string]: { [key: string]: any };
    }) {
        // Some components have had their state changed. This may affect the
        // tree, as their children may have changed.
        //
        // Rebuild the tree
        this.buildTree();

        // The component tree has been modified. Browsers struggle to retrieve
        // the new elements immediately, so wait a bit.
        setTimeout(() => {
            // Flash all changed components
            for (let componentId in deltaStates) {
                // Get the element. Not everything will show up, since some
                // components aren't displayed in the tree (internals).
                let element = document.getElementById(
                    `rio-debugger-component-tree-item-rio-id-${componentId}`
                );

                if (element === null) {
                    continue;
                }

                let elementHeader = element.firstElementChild as HTMLElement;

                // Flash the font to indicate a change
                elementHeader.classList.add(
                    'rio-debugger-component-tree-flash'
                );

                setTimeout(() => {
                    elementHeader.classList.remove(
                        'rio-debugger-component-tree-flash'
                    );
                }, 5000);
            }
        }, 0);
    }
}
