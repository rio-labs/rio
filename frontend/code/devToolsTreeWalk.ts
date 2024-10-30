/// The devtools frequently need to display the component tree. When presenting
/// it to the user, they like to pretend that the internal & injected nodes
/// don't exist. This module contains the logic for walking the tree and
/// filtering out the nodes that shouldn't be displayed.

import { componentsById, getRootComponent } from "./componentManagement";
import { ComponentBase } from "./components/componentBase";
import { HighLevelComponent } from "./components/highLevelComponent";

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

/// Return the root component, but take care to discard any rio internal
/// components.
export function getDisplayedRootComponent(): ComponentBase {
    let fundamentalRootComponent = getRootComponent();

    let userRootComponent =
        componentsById[fundamentalRootComponent.state.content]!;

    return userRootComponent;
}
