import { AlignComponent } from './components/align';
import { BuildFailedComponent } from './components/buildFailed';
import { ButtonComponent } from './components/button';
import { CardComponent } from './components/card';
import { ClassContainerComponent } from './components/classContainer';
import { CodeBlockComponent } from './components/codeBlock';
import { CodeExplorerComponent } from './components/codeExplorer';
import { ColorPickerComponent } from './components/colorPicker';
import { ColumnComponent, RowComponent } from './components/linearContainers';
import { ComponentBase, ComponentState } from './components/componentBase';
import { ComponentId } from './dataModels';
import { ComponentTreeComponent } from './components/componentTree';
import { CustomListItemComponent } from './components/customListItem';
import { DebuggerConnectorComponent } from './components/debuggerConnector';
import { DrawerComponent } from './components/drawer';
import { DropdownComponent } from './components/dropdown';
import { FlowComponent as FlowContainerComponent } from './components/flowContainer';
import { FundamentalRootComponent } from './components/fundamentalRootComponent';
import { GridComponent } from './components/grid';
import { HeadingListItemComponent } from './components/headingListItem';
import { HtmlComponent } from './components/html';
import { IconComponent } from './components/icon';
import { ImageComponent } from './components/image';
import { KeyEventListenerComponent } from './components/keyEventListener';
import { LinkComponent } from './components/link';
import { ListViewComponent } from './components/listView';
import { MarginComponent } from './components/margin';
import { MarkdownComponent } from './components/markdown';
import { MediaPlayerComponent } from './components/mediaPlayer';
import { MouseEventListenerComponent } from './components/mouseEventListener';
import { MultiLineTextInputComponent } from './components/multiLineTextInput';
import { NodeInputComponent } from './components/nodeInput';
import { NodeOutputComponent } from './components/nodeOutput';
import { OverlayComponent } from './components/overlay';
import { PlaceholderComponent } from './components/placeholder';
import { PlotComponent } from './components/plot';
import { PopupComponent } from './components/popup';
import { ProgressBarComponent } from './components/progressBar';
import { ProgressCircleComponent } from './components/progressCircle';
import { RectangleComponent } from './components/rectangle';
import { reprElement, scrollToUrlFragment } from './utils';
import { RevealerComponent } from './components/revealer';
import { ScrollContainerComponent } from './components/scrollContainer';
import { ScrollTargetComponent } from './components/scrollTarget';
import { SeparatorComponent } from './components/separator';
import { SeparatorListItemComponent } from './components/separatorListItem';
import { SliderComponent } from './components/slider';
import { SlideshowComponent } from './components/slideshow';
import { StackComponent } from './components/stack';
import { SwitchComponent } from './components/switch';
import { SwitcherBarComponent } from './components/switcherBar';
import { SwitcherComponent } from './components/switcher';
import { TableComponent } from './components/table';
import { TextComponent } from './components/text';
import { TextInputComponent } from './components/textInput';
import { ThemeContextSwitcherComponent } from './components/themeContextSwitcher';
import { TooltipComponent } from './components/tooltip';
import { updateLayout } from './layouting';

const COMPONENT_CLASSES = {
    'Align-builtin': AlignComponent,
    'BuildFailed-builtin': BuildFailedComponent,
    'Button-builtin': ButtonComponent,
    'Card-builtin': CardComponent,
    'ClassContainer-builtin': ClassContainerComponent,
    'CodeBlock-builtin': CodeBlockComponent,
    'CodeExplorer-builtin': CodeExplorerComponent,
    'ColorPicker-builtin': ColorPickerComponent,
    'Column-builtin': ColumnComponent,
    'ComponentTree-builtin': ComponentTreeComponent,
    'CustomListItem-builtin': CustomListItemComponent,
    'DebuggerConnector-builtin': DebuggerConnectorComponent,
    'Drawer-builtin': DrawerComponent,
    'Dropdown-builtin': DropdownComponent,
    'FlowContainer-builtin': FlowContainerComponent,
    'FundamentalRootComponent-builtin': FundamentalRootComponent,
    'Grid-builtin': GridComponent,
    'HeadingListItem-builtin': HeadingListItemComponent,
    'Html-builtin': HtmlComponent,
    'Icon-builtin': IconComponent,
    'Image-builtin': ImageComponent,
    'KeyEventListener-builtin': KeyEventListenerComponent,
    'Link-builtin': LinkComponent,
    'ListView-builtin': ListViewComponent,
    'Margin-builtin': MarginComponent,
    'Markdown-builtin': MarkdownComponent,
    'MediaPlayer-builtin': MediaPlayerComponent,
    'MouseEventListener-builtin': MouseEventListenerComponent,
    'MultiLineTextInput-builtin': MultiLineTextInputComponent,
    'NodeInput-builtin': NodeInputComponent,
    'NodeOutput-builtin': NodeOutputComponent,
    'Overlay-builtin': OverlayComponent,
    'Plot-builtin': PlotComponent,
    'Popup-builtin': PopupComponent,
    'ProgressBar-builtin': ProgressBarComponent,
    'ProgressCircle-builtin': ProgressCircleComponent,
    'Rectangle-builtin': RectangleComponent,
    'Revealer-builtin': RevealerComponent,
    'Row-builtin': RowComponent,
    'ScrollContainer-builtin': ScrollContainerComponent,
    'ScrollTarget-builtin': ScrollTargetComponent,
    'Separator-builtin': SeparatorComponent,
    'SeparatorListItem-builtin': SeparatorListItemComponent,
    'Slider-builtin': SliderComponent,
    'Slideshow-builtin': SlideshowComponent,
    'Stack-builtin': StackComponent,
    'Switch-builtin': SwitchComponent,
    'Switcher-builtin': SwitcherComponent,
    'SwitcherBar-builtin': SwitcherBarComponent,
    'Table-builtin': TableComponent,
    'Text-builtin': TextComponent,
    'TextInput-builtin': TextInputComponent,
    'ThemeContextSwitcher-builtin': ThemeContextSwitcherComponent,
    'Tooltip-builtin': TooltipComponent,
    Placeholder: PlaceholderComponent,
};

globalThis.COMPONENT_CLASSES = COMPONENT_CLASSES;

export const componentsById: { [id: ComponentId]: ComponentBase | undefined } =
    {};

export const componentsByElement = new Map<HTMLElement, ComponentBase>();

export function getRootComponent(): FundamentalRootComponent {
    let element = document.body.querySelector(
        '.rio-fundamental-root-component'
    );
    console.assert(
        element !== null,
        "Couldn't find the root component in the document body"
    );
    return componentsByElement.get(
        element as HTMLElement
    ) as FundamentalRootComponent;
}

export function getRootScroller(): ScrollContainerComponent {
    let rootComponent = getRootComponent();
    return componentsById[
        rootComponent.state.content
    ] as ScrollContainerComponent;
}

globalThis.getRootScroller = getRootScroller; // Used to scroll up after navigating to a different page

export function getComponentByElement(element: Element): ComponentBase {
    let instance = tryGetComponentByElement(element);

    if (instance === null) {
        // Just displaying the element itself isn't quite enough information for
        // debugging. We'll go up the tree until we find an element that belongs
        // to a component, and include that in the error message.
        let elem: Element | null = element.parentElement;
        while (elem) {
            instance = tryGetComponentByElement(elem);
            if (instance !== null) {
                throw `Element ${reprElement(
                    element
                )} does not correspond to a component. It is a child element of ${instance.toString()}`;
            }

            elem = elem.parentElement;
        }

        throw `Element ${reprElement(
            element
        )} does not correspond to a component (and none of its parent elements correspond to a component, either)`;
    }

    return instance;
}

globalThis.componentsById = componentsById; // For debugging
globalThis.getInstanceByElement = getComponentByElement; // For debugging

export function tryGetComponentByElement(
    element: Element
): ComponentBase | null {
    return componentsByElement.get(element as HTMLElement) ?? null;
}

export function isComponentElement(element: Element): boolean {
    return componentsByElement.has(element as HTMLElement);
}

export function getParentComponentElementIncludingInjected(
    element: HTMLElement
): HTMLElement | null {
    let curElement = element.parentElement;

    while (curElement !== null) {
        if (isComponentElement(curElement)) {
            return curElement;
        }

        curElement = curElement.parentElement;
    }

    return null;
}

function getCurrentComponentState(
    id: ComponentId,
    deltaState: ComponentState
): ComponentState {
    let instance = componentsById[id];

    if (instance === undefined) {
        return deltaState;
    }

    return {
        ...instance.state,
        ...deltaState,
    };
}

function createLayoutComponentStates(
    componentId: ComponentId,
    message: { [id: string]: ComponentState }
): ComponentId {
    let deltaState = message[componentId] || {};
    let entireState = getCurrentComponentState(componentId, deltaState);
    let resultId = componentId;

    // Margin
    let margin = entireState['_margin_']!;
    if (margin === undefined) {
        console.error(`Got incomplete state for component ${componentId}`);
    }
    if (
        margin[0] !== 0 ||
        margin[1] !== 0 ||
        margin[2] !== 0 ||
        margin[3] !== 0
    ) {
        let marginId = (componentId * -10) as ComponentId;
        message[marginId] = {
            _type_: 'Margin-builtin',
            _python_type_: 'Margin (injected)',
            _key_: null,
            _margin_: [0, 0, 0, 0],
            _size_: [0, 0],
            _grow_: entireState._grow_,
            _rio_internal_: true,
            // @ts-ignore
            content: resultId,
            margin_left: margin[0],
            margin_top: margin[1],
            margin_right: margin[2],
            margin_bottom: margin[3],
        };
        resultId = marginId;
    }

    // Align
    let align = entireState['_align_']!;
    if (align === undefined) {
        console.error(`Got incomplete state for component ${componentId}`);
    }
    if (align[0] !== null || align[1] !== null) {
        let alignId = (componentId * -10 - 1) as ComponentId;
        message[alignId] = {
            _type_: 'Align-builtin',
            _python_type_: 'Align (injected)',
            _key_: null,
            _margin_: [0, 0, 0, 0],
            _size_: [0, 0],
            _grow_: entireState._grow_,
            _rio_internal_: true,
            // @ts-ignore
            content: resultId,
            align_x: align[0],
            align_y: align[1],
        };
        resultId = alignId;
    }

    return resultId;
}

/// Given a state, return the ids of all its children
export function getChildIds(state: ComponentState): ComponentId[] {
    let result: ComponentId[] = [];

    let propertyNamesWithChildren =
        globalThis.CHILD_ATTRIBUTE_NAMES[state['_type_']!] || [];

    for (let propertyName of propertyNamesWithChildren) {
        let propertyValue = state[propertyName];

        if (Array.isArray(propertyValue)) {
            result.push(...propertyValue);
        } else if (propertyValue !== null && propertyValue !== undefined) {
            result.push(propertyValue);
        }
    }

    return result;
}

function replaceChildrenWithLayoutComponents(
    deltaState: ComponentState,
    childIds: Set<ComponentId>,
    message: { [id: string]: ComponentState }
): void {
    let propertyNamesWithChildren =
        globalThis.CHILD_ATTRIBUTE_NAMES[deltaState['_type_']!] || [];

    function uninjectedId(id: ComponentId): ComponentId {
        if (id >= 0) {
            return id;
        }

        return Math.floor(id / -10) as ComponentId;
    }

    for (let propertyName of propertyNamesWithChildren) {
        let propertyValue = deltaState[propertyName] as
            | ComponentId[]
            | ComponentId
            | null
            | undefined;

        if (Array.isArray(propertyValue)) {
            deltaState[propertyName] = propertyValue.map(
                (childId: ComponentId): ComponentId => {
                    childId = uninjectedId(childId);
                    childIds.add(childId);
                    return createLayoutComponentStates(childId, message);
                }
            );
        } else if (propertyValue !== null && propertyValue !== undefined) {
            let childId = uninjectedId(propertyValue);
            deltaState[propertyName] = createLayoutComponentStates(
                childId,
                message
            );
            childIds.add(childId);
        }
    }
}

function preprocessDeltaStates(message: {
    [id: string]: ComponentState;
}): void {
    // Fortunately the root component is created internally by the server, so we
    // don't need to worry about it having a margin or alignment.

    let originalComponentIds = Object.keys(message).map((id) =>
        parseInt(id)
    ) as ComponentId[];

    // Keep track of which components have their parents in the message
    let childIds: Set<ComponentId> = new Set();

    // Walk over all components in the message and inject layout components. The
    // message is modified in-place, so take care to have a copy of all keys
    // (`originalComponentIds`)
    for (let componentId of originalComponentIds) {
        replaceChildrenWithLayoutComponents(
            message[componentId],
            childIds,
            message
        );
    }

    // Find all components which have had a layout component injected, and make
    // sure their parents are updated to point to the new component.
    for (let componentId of originalComponentIds) {
        // Child of another component in the message
        if (childIds.has(componentId)) {
            continue;
        }

        // The parent isn't contained in the message. Find and add it.
        let child = componentsById[componentId];
        if (child === undefined) {
            continue;
        }

        let parent = child.getParentExcludingInjected();
        if (parent === null) {
            continue;
        }

        let newParentState = { ...parent.state };
        replaceChildrenWithLayoutComponents(newParentState, childIds, message);
        message[parent.id] = newParentState;
    }
}

export function updateComponentStates(
    deltaStates: { [id: string]: ComponentState },
    rootComponentId: ComponentId | null
): void {
    // Preprocess the message. This converts `_align_` and `_margin_` properties
    // into actual components, amongst other things.
    preprocessDeltaStates(deltaStates);

    // Modifying the DOM makes the keyboard focus get lost. Remember which
    // element had focus so we can restore it later.
    let focusedElement = document.activeElement;
    // Find the component that this HTMLElement belongs to
    while (focusedElement !== null && !isComponentElement(focusedElement)) {
        focusedElement = focusedElement.parentElement;
    }
    let focusedComponent =
        focusedElement === null
            ? null
            : getComponentByElement(focusedElement as HTMLElement);

    // Create a HTML element to hold all latent components, so they aren't
    // garbage collected while updating the DOM.
    let latentComponents = new Set<ComponentBase>();

    // Make sure all components mentioned in the message have a corresponding HTML
    // element
    for (let componentIdAsString in deltaStates) {
        let deltaState = deltaStates[componentIdAsString];
        let component = componentsById[componentIdAsString];

        // This is a reused component, no need to instantiate a new one
        if (component) {
            continue;
        }

        // Get the class for this component
        const componentClass = COMPONENT_CLASSES[deltaState._type_!];

        // Make sure the component type is valid (Just helpful for debugging)
        if (!componentClass) {
            throw `Encountered unknown component type: ${deltaState._type_}`;
        }

        // Create an instance for this component
        let newComponent: ComponentBase = new componentClass(
            parseInt(componentIdAsString),
            deltaState
        );

        // Register the component for quick and easy lookup
        componentsById[componentIdAsString] = newComponent;
        componentsByElement.set(newComponent.element, newComponent);

        // Store the component's class name in the element. Used for debugging.
        newComponent.element.setAttribute(
            'dbg-py-class',
            deltaState._python_type_!
        );
        newComponent.element.setAttribute('dbg-id', componentIdAsString);

        // Set the component's key, if it has one. Used for debugging.
        let key = deltaState['key'];
        if (key !== undefined) {
            newComponent.element.setAttribute('dbg-key', `${key}`);
        }
    }

    // Update all components mentioned in the message
    for (let id in deltaStates) {
        let deltaState = deltaStates[id];
        let component: ComponentBase = componentsById[id]!;

        // Perform updates specific to this component type
        component.updateElement(deltaState, latentComponents);

        // If the component's width or height has changed, request a re-layout.
        let width_changed =
            Math.abs(deltaState._size_![0] - component.state._size_[0]) > 1e-6;
        let height_changed =
            Math.abs(deltaState._size_![1] - component.state._size_[1]) > 1e-6;

        if (width_changed || height_changed) {
            console.log(
                `Triggering re-layout because component #${id} changed size: ${component.state._size_} -> ${deltaState._size_}`
            );
            component.makeLayoutDirty();
        }

        // Update the component's state
        component.state = {
            ...component.state,
            ...deltaState,
        };
    }

    // Set the root component if necessary
    if (rootComponentId !== null) {
        let rootElement = componentsById[rootComponentId]!.element;
        document.body.appendChild(rootElement);
    }

    // Restore the keyboard focus
    if (focusedComponent !== null) {
        restoreKeyboardFocus(focusedComponent, latentComponents);
    }

    // Remove the latent components
    for (let component of latentComponents) {
        // Destruct the component and all its children
        let queue = [component];

        for (let comp of queue) {
            queue.push(...comp.children);

            comp.onDestruction();
            delete componentsById[comp.id];
            componentsByElement.delete(comp.element);
        }
    }

    // Update the layout
    updateLayout();

    // If this is the first time, check if there's an #url-fragment and scroll
    // to it
    if (rootComponentId !== null) {
        scrollToUrlFragment();
    }
}

function canHaveKeyboardFocus(instance: ComponentBase): boolean {
    // @ts-expect-error
    return typeof instance.grabKeyboardFocus === 'function';
}

function restoreKeyboardFocus(
    focusedComponent: ComponentBase,
    latentComponents: Set<ComponentBase>
): void {
    // The elements that are about to die still know the id of the parent from
    // which they were just removed. We'll go up the tree until we find a parent
    // that can accept the keyboard focus.
    //
    // Keep in mind that we have to traverse the component tree all the way up to
    // the root. Because even if a component still has a parent, the parent itself
    // might be about to die.
    let rootComponent = getRootComponent();
    let current = focusedComponent;
    let winner: ComponentBase | null = null;

    while (current !== rootComponent) {
        // If this component is dead, no child of it can get the keyboard focus
        if (latentComponents.has(current)) {
            winner = null;
        }

        // If we don't currently know of a focusable (and live) component, check
        // if this one fits the bill
        else if (winner === null && canHaveKeyboardFocus(current)) {
            winner = current;
        }

        current = current.parent!;
    }

    // We made it to the root. Do we have a winner?
    if (winner !== null) {
        // @ts-expect-error
        winner.grabKeyboardFocus();
    }
}
