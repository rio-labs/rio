import { ButtonComponent, IconButtonComponent } from "./components/buttons";
import { CalendarComponent } from "./components/calendar";
import { CardComponent } from "./components/card";
import { CheckboxComponent } from "./components/checkbox";
import { ClassContainerComponent } from "./components/classContainer";
import { CodeBlockComponent } from "./components/codeBlock";
import { CodeExplorerComponent } from "./components/codeExplorer";
import { ColorPickerComponent } from "./components/colorPicker";
import { ColumnComponent, RowComponent } from "./components/linearContainers";
import {
    ComponentBase,
    DeltaStateFromBackend,
} from "./components/componentBase";
import { ComponentId } from "./dataModels";
import { ComponentPickerComponent } from "./components/componentPicker";
import { ComponentTreeComponent } from "./components/componentTree";
import { CustomTreeItemComponent } from "./components/customTreeItem";
import { devToolsConnector } from "./app";
import { DevToolsConnectorComponent } from "./components/devToolsConnector";
import { DialogContainerComponent } from "./components/dialogContainer";
import { DrawerComponent } from "./components/drawer";
import { DropdownComponent } from "./components/dropdown";
import { ErrorPlaceholderComponent } from "./components/errorPlaceholder";
import { FilePickerAreaComponent } from "./components/filePickerArea";
import { FlowComponent as FlowContainerComponent } from "./components/flowContainer";
import { FundamentalRootComponent } from "./components/fundamentalRootComponent";
import { GridComponent } from "./components/grid";
import {
    CustomListItemComponent,
    HeadingListItemComponent,
    SeparatorListItemComponent,
} from "./components/listItems";
import { HighLevelComponent as HighLevelComponent } from "./components/highLevelComponent";
import { IconComponent } from "./components/icon";
import { ImageComponent } from "./components/image";
import { KeyEventListenerComponent } from "./components/keyEventListener";
import { LayoutDisplayComponent } from "./components/layoutDisplay";
import { LinkComponent } from "./components/link";
import { ListViewComponent } from "./components/listView";
import { MarkdownComponent } from "./components/markdown";
import { MediaPlayerComponent } from "./components/mediaPlayer";
import { MouseEventListenerComponent } from "./components/mouseEventListener";
import { MultiLineTextInputComponent } from "./components/multiLineTextInput";
import { NodeInputComponent } from "./components/nodeInput";
import { NodeOutputComponent } from "./components/nodeOutput";
import { OverlayComponent } from "./components/overlay";
import { PdfViewerComponent } from "./components/pdf_viewer";
import { PlotComponent } from "./components/plot";
import { PointerEventListenerComponent } from "./components/pointerEventListener";
import { PopupComponent } from "./components/popup";
import { ProgressBarComponent } from "./components/progressBar";
import { ProgressCircleComponent } from "./components/progressCircle";
import { RectangleComponent } from "./components/rectangle";
import { reprElement, scrollToUrlFragment } from "./utils";
import { RevealerComponent } from "./components/revealer";
import { ScrollContainerComponent } from "./components/scrollContainer";
import { ScrollTargetComponent } from "./components/scrollTarget";
import { SeparatorComponent } from "./components/separator";
import { SliderComponent } from "./components/slider";
import { SlideshowComponent } from "./components/slideshow";
import { StackComponent } from "./components/stack";
import { SwitchComponent } from "./components/switch";
import { SwitcherBarComponent } from "./components/switcherBar";
import { SwitcherComponent } from "./components/switcher";
import { TableComponent } from "./components/table";
import { TextComponent } from "./components/text";
import { TextInputComponent } from "./components/textInput";
import { ThemeContextSwitcherComponent } from "./components/themeContextSwitcher";
import { TooltipComponent } from "./components/tooltip";
import { WebviewComponent } from "./components/webview";
import { GraphEditorComponent } from "./components/graphEditor/graphEditor";
import { KeyboardFocusableComponent } from "./components/keyboardFocusableComponent";
import { NumberInputComponent } from "./components/numberInput";

const COMPONENT_CLASSES = {
    "Button-builtin": ButtonComponent,
    "Calendar-builtin": CalendarComponent,
    "Card-builtin": CardComponent,
    "Checkbox-builtin": CheckboxComponent,
    "ClassContainer-builtin": ClassContainerComponent,
    "CodeBlock-builtin": CodeBlockComponent,
    "CodeExplorer-builtin": CodeExplorerComponent,
    "ColorPicker-builtin": ColorPickerComponent,
    "Column-builtin": ColumnComponent,
    "ComponentPicker-builtin": ComponentPickerComponent,
    "ComponentTree-builtin": ComponentTreeComponent,
    "CustomListItem-builtin": CustomListItemComponent,
    "CustomTreeItem-builtin": CustomTreeItemComponent,
    "DevToolsConnector-builtin": DevToolsConnectorComponent,
    "DialogContainer-builtin": DialogContainerComponent,
    "Drawer-builtin": DrawerComponent,
    "Dropdown-builtin": DropdownComponent,
    "ErrorPlaceholder-builtin": ErrorPlaceholderComponent,
    "FilePickerArea-builtin": FilePickerAreaComponent,
    "FlowContainer-builtin": FlowContainerComponent,
    "FundamentalRootComponent-builtin": FundamentalRootComponent,
    "GraphEditor-builtin": GraphEditorComponent,
    "Grid-builtin": GridComponent,
    "HeadingListItem-builtin": HeadingListItemComponent,
    "HighLevelComponent-builtin": HighLevelComponent,
    "Icon-builtin": IconComponent,
    "IconButton-builtin": IconButtonComponent,
    "Image-builtin": ImageComponent,
    "KeyEventListener-builtin": KeyEventListenerComponent,
    "LayoutDisplay-builtin": LayoutDisplayComponent,
    "Link-builtin": LinkComponent,
    "ListView-builtin": ListViewComponent,
    "Markdown-builtin": MarkdownComponent,
    "MediaPlayer-builtin": MediaPlayerComponent,
    "MouseEventListener-builtin": MouseEventListenerComponent,
    "MultiLineTextInput-builtin": MultiLineTextInputComponent,
    "NodeInput-builtin": NodeInputComponent,
    "NodeOutput-builtin": NodeOutputComponent,
    "NumberInput-builtin": NumberInputComponent,
    "Overlay-builtin": OverlayComponent,
    "PdfViewer-builtin": PdfViewerComponent,
    "Plot-builtin": PlotComponent,
    "PointerEventListener-builtin": PointerEventListenerComponent,
    "Popup-builtin": PopupComponent,
    "ProgressBar-builtin": ProgressBarComponent,
    "ProgressCircle-builtin": ProgressCircleComponent,
    "Rectangle-builtin": RectangleComponent,
    "Revealer-builtin": RevealerComponent,
    "Row-builtin": RowComponent,
    "ScrollContainer-builtin": ScrollContainerComponent,
    "ScrollTarget-builtin": ScrollTargetComponent,
    "Separator-builtin": SeparatorComponent,
    "SeparatorListItem-builtin": SeparatorListItemComponent,
    "Slider-builtin": SliderComponent,
    "Slideshow-builtin": SlideshowComponent,
    "Stack-builtin": StackComponent,
    "Switch-builtin": SwitchComponent,
    "Switcher-builtin": SwitcherComponent,
    "SwitcherBar-builtin": SwitcherBarComponent,
    "Table-builtin": TableComponent,
    "Text-builtin": TextComponent,
    "TextInput-builtin": TextInputComponent,
    "ThemeContextSwitcher-builtin": ThemeContextSwitcherComponent,
    "Tooltip-builtin": TooltipComponent,
    "Webview-builtin": WebviewComponent,
};

globalThis.COMPONENT_CLASSES = COMPONENT_CLASSES;

export const componentsById: { [id: ComponentId]: ComponentBase | undefined } =
    {};

export const componentsByElement = new Map<HTMLElement, ComponentBase>();

let fundamentalRootComponent: FundamentalRootComponent | null = null;

export function getRootComponent(): FundamentalRootComponent {
    if (fundamentalRootComponent === null) {
        throw new Error("There is no root component yet");
    }

    return fundamentalRootComponent;
}

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
globalThis.getComponentByElement = getComponentByElement; // For debugging

export function tryGetComponentByElement(
    element: Element
): ComponentBase | null {
    let component = componentsByElement.get(element as HTMLElement);
    if (component !== undefined) {
        return component;
    }

    // Components may create additional HTML elements for layouting purposes
    // (alignment, scrolling, ...), so check if this is such an element
    if (element instanceof HTMLElement) {
        let ownerId = element.dataset.ownerId;

        if (ownerId !== undefined) {
            component = componentsById[ownerId];

            if (component !== undefined) {
                return component;
            }
        }
    }

    return null;
}

export function isComponentElement(element: Element): boolean {
    return componentsByElement.has(element as HTMLElement);
}

export function getParentComponentElement(
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

/// Given a state, return the ids of all its children
export function getChildIds(state: DeltaStateFromBackend): ComponentId[] {
    let result: ComponentId[] = [];

    let propertyNamesWithChildren =
        globalThis.CHILD_ATTRIBUTE_NAMES[state._type_!] || [];

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

export function updateComponentStates(
    deltaStates: { [id: string]: DeltaStateFromBackend },
    rootComponentId: ComponentId | null
): void {
    // Modifying the DOM makes the keyboard focus get lost. Remember which
    // element had focus so we can restore it later.
    let focusedElement = document.activeElement;
    // Find the component that this element belongs to
    while (focusedElement !== null && !isComponentElement(focusedElement)) {
        focusedElement = focusedElement.parentElement;
    }
    let focusedComponent =
        focusedElement === null ? null : getComponentByElement(focusedElement);

    let context = new ComponentStatesUpdateContext();

    // Keep track of all components whose `_grow_` changed, because their
    // parents have to be notified so they can update their CSS
    let growChangedComponents: ComponentBase[] = [];

    // Make sure all components mentioned in the message have a corresponding
    // HTML element
    for (let componentIdAsString in deltaStates) {
        let deltaState = deltaStates[componentIdAsString];
        let component = componentsById[componentIdAsString];

        // This is a reused component, no need to instantiate a new one
        if (component) {
            // Check if its `_grow_` changed
            if (deltaState._grow_ !== undefined) {
                if (
                    deltaState._grow_[0] !== component.state._grow_[0] ||
                    deltaState._grow_[1] !== component.state._grow_[1]
                ) {
                    growChangedComponents.push(component);
                }
            }
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
            deltaState,
            context
        );

        // Register the component for quick and easy lookup
        componentsById[componentIdAsString] = newComponent;
        componentsByElement.set(newComponent.element, newComponent);

        // Store the component's class name in the element. Used for debugging.
        newComponent.element.setAttribute(
            "dbg-py-class",
            deltaState._python_type_!
        );
        newComponent.element.setAttribute("dbg-id", componentIdAsString);

        // Set the component's key, if it has one. Used for debugging.
        let key = deltaState["key"];
        if (key !== undefined) {
            newComponent.element.setAttribute("dbg-key", `${key}`);
        }
    }

    // Some components, like Overlays, need access to the root component. If it
    // changed, assign it to our global variable.
    if (rootComponentId !== null) {
        fundamentalRootComponent = componentsById[
            rootComponentId
        ] as FundamentalRootComponent;
    }

    // Update all components mentioned in the message
    for (let id in deltaStates) {
        let deltaState = deltaStates[id];
        let component: ComponentBase = componentsById[id]!;

        // Perform updates specific to this component type
        component.updateElement(deltaState, context);

        // Update the component's state
        Object.assign(component.state, deltaState);
    }

    // Notify the parents of all elements whose `_grow_` changed to update their
    // CSS
    let parents = new Set<ComponentBase>();
    for (let child of growChangedComponents) {
        parents.add(child.parent!);
    }
    for (let parent of parents) {
        parent.onChildGrowChanged();
    }

    context.dispatchEvent(new Event("all states updated"));

    // Restore the keyboard focus
    if (focusedComponent !== null) {
        restoreKeyboardFocus(focusedElement, focusedComponent, context);
    }

    // Remove the latent components
    for (let component of context.latentComponents) {
        // Dialog containers aren't part of the component tree, so they falsely
        // appear as latent. Don't destroy them.
        if (component instanceof DialogContainerComponent) {
            continue;
        }

        recursivelyDeleteComponent(component);
    }

    // If this is the first time, check if there's an #url-fragment and scroll
    // to it
    if (rootComponentId !== null) {
        scrollToUrlFragment("instant");
    }

    // Notify the dev tools, if any
    if (devToolsConnector !== null) {
        devToolsConnector.afterComponentStateChange(deltaStates);
    }
}

export function recursivelyDeleteComponent(component: ComponentBase): void {
    let to_do = [component];

    for (let comp of to_do) {
        // Make sure the children will be cleaned up as well
        to_do.push(...comp.children);

        // Inform the component of its impending doom
        comp.onDestruction();

        // Remove it from the global lookup tables
        delete componentsById[comp.id];
        componentsByElement.delete(comp.element);
    }

    // And finally, remove it from the DOM
    component.element.remove();
}

function restoreKeyboardFocus(
    focusedElement: Element,
    focusedComponent: ComponentBase,
    context: ComponentStatesUpdateContext
): void {
    // If we can keep the focus in the same element, do that
    if (focusedElement instanceof HTMLElement && focusedElement.isConnected) {
        if (document.activeElement !== focusedElement) {
            focusedElement.focus();
        }
        return;
    }

    // The elements that are about to die still know the id of the parent from
    // which they were just removed. We'll go up the tree until we find a parent
    // that can accept the keyboard focus.
    //
    // Keep in mind that we have to traverse the component tree all the way up
    // to the root. Because even if a component still has a parent, the parent
    // itself might be about to die.
    let rootComponent = getRootComponent();
    let current = focusedComponent;
    let winner: KeyboardFocusableComponent | null = null;

    while (current !== rootComponent) {
        // If this component is dead, no child of it can get the keyboard focus
        if (context.latentComponents.has(current)) {
            winner = null;
        }

        // If we don't currently know of a focusable (and live) component, check
        // if this one fits the bill
        else if (
            winner === null &&
            current instanceof KeyboardFocusableComponent
        ) {
            winner = current;
        }

        current = current.parent!;
    }

    // We made it to the root. Do we have a winner?
    if (winner !== null) {
        winner.grabKeyboardFocus();
    }
}

export class ComponentStatesUpdateContext extends EventTarget {
    // A set to hold all latent components, so they aren't garbage collected
    // while updating the DOM.
    public latentComponents = new Set<ComponentBase>();

    public addEventListener(
        type: "all states updated",
        callback: EventListenerOrEventListenerObject | null,
        options?: AddEventListenerOptions | boolean
    ): void {
        super.addEventListener(type, callback, options);
    }
}
