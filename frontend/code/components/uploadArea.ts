import { applySwitcheroo } from '../designApplication';
import { ComponentBase, ComponentState } from './componentBase';
import { RippleEffect } from '../rippleEffect';
import { markEventAsHandled } from '../eventHandling';

type UploadAreaState = ComponentState & {
    _type_: 'UploadArea-builtin';
};

export class UploadAreaComponent extends ComponentBase {
    state: Required<UploadAreaState>;

    private fileInput: HTMLInputElement;
    private childContainer: HTMLElement;

    private rippleInstance: RippleEffect;

    createElement(): HTMLElement {
        // Create the element
        let element = document.createElement('div');
        element.classList.add('rio-upload-area');

        // Create the child container
        this.childContainer = document.createElement('div');
        element.appendChild(this.childContainer);

        // A hidden file input
        this.fileInput = document.createElement('input');
        this.fileInput.type = 'file';
        element.appendChild(this.fileInput);

        // Add a material ripple effect
        this.rippleInstance = new RippleEffect(element, {
            triggerOnPress: false,
        });

        // Connect event handlers
        //
        // Highlight drop area when dragging files over it
        ['dragenter', 'dragover'].forEach((eventName) => {
            element.addEventListener(
                eventName,
                (event) => {
                    event.preventDefault();
                    event.stopPropagation();

                    const dragEvent = event as DragEvent;
                    const rect = element.getBoundingClientRect();
                    const x = dragEvent.clientX - rect.left;
                    const y = dragEvent.clientY - rect.top;

                    element.style.setProperty('--x', `${x}px`);
                    element.style.setProperty('--y', `${y}px`);
                    element.classList.add('rio-upload-area-file-hover');
                },
                false
            );
        });

        ['dragleave', 'drop'].forEach((eventName) => {
            element.addEventListener(
                eventName,
                (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    element.classList.remove('rio-upload-area-file-hover');
                },
                false
            );
        });

        // Handle dropped files
        element.addEventListener(
            'drop',
            (event: DragEvent) => {
                // Why can this be null?
                if (event.dataTransfer == null) {
                    return;
                }

                // Trigger the ripple effect
                this.rippleInstance.trigger(event);

                // Upload the file(s)
                const files = event.dataTransfer.files;
                this.uploadFiles(files);
            },
            false
        );

        // Open file chooser when clicking the drop area
        element.addEventListener('click', () => {
            this.fileInput.click();
        });

        // Handle files selected from the file input
        this.fileInput.addEventListener('change', (e) => {
            // const files = e.target.files;
            // this.uploadFiles(files);
        });

        return element;
    }

    updateElement(
        deltaState: UploadAreaState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);
    }

    uploadFiles(files) {
        [...files].forEach((file) => {
            console.log(file.name);
            // Add any further file handling logic here
        });
    }
}
