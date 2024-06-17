import { pixelsPerRem } from './app';
import { getRootComponent } from './componentManagement';
import { ComponentBase } from './components/componentBase';
import {
    UnittestClientLayoutInfo,
    UnittestComponentLayout,
} from './dataModels';

function dumpComponentRecursively(
    component: ComponentBase,
    componentLayouts: { [componentId: number]: UnittestComponentLayout }
) {
    // Prepare the layout
    const layout = {} as UnittestComponentLayout;

    // Get layout information from the component
    const rect = component.element.getBoundingClientRect();

    layout.leftInViewport = rect.left / pixelsPerRem;
    layout.topInViewport = rect.top / pixelsPerRem;

    layout.naturalWidth = component.element.scrollWidth / pixelsPerRem;
    layout.naturalHeight = component.element.scrollHeight / pixelsPerRem;

    layout.requestedWidth = Math.max(
        layout.naturalWidth,
        component.state._size_[0]
    );
    layout.requestedHeight = Math.max(
        layout.naturalHeight,
        component.state._size_[1]
    );

    layout.allocatedWidth = rect.width / pixelsPerRem;
    layout.allocatedHeight = rect.height / pixelsPerRem;

    layout.aux = {};

    // Save the layout
    componentLayouts[component.id] = layout;

    // Recurse into children
    for (let child of component.children) {
        dumpComponentRecursively(child, componentLayouts);
    }
}

export function getUnittestClientLayoutInfo(): UnittestClientLayoutInfo {
    // Prepare the result
    const result = {} as UnittestClientLayoutInfo;

    result.windowWidth = window.innerWidth / pixelsPerRem;
    result.windowHeight = window.innerHeight / pixelsPerRem;

    result.componentLayouts = {};

    // Dump recursively, starting with the root component
    let rootComponent = getRootComponent();
    dumpComponentRecursively(rootComponent, result.componentLayouts);

    // Done!
    return result;
}
