/// The devtools frequently need to display the component tree. When presenting
/// it to the user, they like to pretend that the internal & injected nodes
/// don't exist. This module contains the logic for walking the tree and
/// filtering out the nodes that shouldn't be displayed.

import { getRootScroller, componentsById } from './componentManagement';
import { ComponentBase } from './components/componentBase';

/// Many of the spawned components are internal to Rio and shouldn't be
/// displayed to the user. This function makes that determination.
export function shouldDisplayComponent(comp: ComponentBase): boolean {
    return !comp.state._rio_internal_;
}

function _drillDown(comp: ComponentBase): ComponentBase[] {
    // Is this component displayable?
    if (shouldDisplayComponent(comp)) {
        return [comp];
    }

    // No, drill down
    let result: ComponentBase[] = [];

    for (let child of comp.children) {
        result.push(..._drillDown(child));
    }

    return result;
}

/// Given a component, return all of its children which should be displayed
/// in the tree.
export function getDisplayableChildren(comp: ComponentBase): ComponentBase[] {
    let result: ComponentBase[] = [];

    // Keep drilling down until a component which should be displayed
    // is encountered
    for (let child of comp.children) {
        result.push(..._drillDown(child));
    }

    return result;
}

/// Given an injected layout component, return its direct child (Which may
/// also be injected!).
export function getDirectChildOfInjectedComponent(
    comp: ComponentBase
): ComponentBase {
    console.assert(comp.isInjectedLayoutComponent());

    // Both Margins and Aligns have a single child, accessible as `content`
    console.assert(
        comp.state._type_ === 'Margin-builtin' ||
            comp.state._type_ === 'Align-builtin'
    );

    let resultId: number = (comp.state as any).content;
    console.assert(resultId !== undefined);

    // Return the component, not ID
    return componentsById[resultId];
}

/// Return the root component, but take care to discard any rio internal
/// components.
export function getDisplayedRootComponent(): ComponentBase {
    let rootScroller = getRootScroller();
    let result = componentsById[rootScroller.state.content]!;

    // This might be the user's root, but could also be injected. Keep
    // digging.
    while (result.isInjectedLayoutComponent()) {
        result = getDirectChildOfInjectedComponent(result);
    }

    return result;
}
