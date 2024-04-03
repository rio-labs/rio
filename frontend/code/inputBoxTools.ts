// Several components share the same overall style: The input box.
//
// This file contains tools helpful for implementing them.

import { ComponentBase } from './components/componentBase';

export const HORIZONTAL_PADDING: number = 0.8;

export function updateInputBoxNaturalWidth(
    component: ComponentBase,
    additionalSpace: number
): void {
    // Enforce a minimum width, common to all input boxes
    let newWidth = Math.max(8, additionalSpace + HORIZONTAL_PADDING * 2);

    // Dirty?
    if (newWidth !== component.naturalWidth) {
        component.naturalWidth = newWidth;
        component.makeLayoutDirty();
    }
}

/// Update the component's natural height property, and make the layout dirty
/// if needed.
export function updateInputBoxNaturalHeight(
    component: ComponentBase,
    label: string,
    additionalSpace: number
) {
    // Calculate the new height. If a label is set, the height needs to increase
    // to make room for it, when floating above the entered text.
    let newHeight = label.length === 0 ? 2.375 : 3.3;
    newHeight += additionalSpace;

    // Dirty?
    if (newHeight !== component.naturalHeight) {
        component.naturalHeight = newHeight;
        component.makeLayoutDirty();
    }
}
