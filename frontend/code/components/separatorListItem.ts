import { ComponentBase, ComponentState } from './componentBase';

export type SeparatorListItemState = ComponentState & {
    _type_: 'SeparatorListItem-builtin';
};

export class SeparatorListItemComponent extends ComponentBase {
    state: Required<SeparatorListItemState>;

    createElement(): HTMLElement {
        return document.createElement('div');
    }
}
