import { applyIcon, applySwitcheroo } from '../designApplication';
import { ComponentBase, ComponentState } from './componentBase';
import { RippleEffect } from '../rippleEffect';

/// Maps MIME types to what sort of file they represent
const EXTENSION_TO_CATEGORY = {
    bmp: 'picture',
    csv: 'data',
    doc: 'document',
    docx: 'document',
    gif: 'picture',
    h5: 'data',
    hdf5: 'data',
    ico: 'picture',
    ini: 'data',
    jpg: 'picture',
    json: 'data',
    jxl: 'picture',
    md: 'document',
    mdb: 'data',
    ods: 'data',
    odt: 'document',
    parquet: 'data',
    pdf: 'document',
    pickle: 'data',
    png: 'picture',
    pptx: 'document',
    svg: 'picture',
    toml: 'data',
    tsv: 'data',
    txt: 'document',
    webp: 'picture',
    xlsx: 'data',
};

/// Maps types of files to
///
/// - A human-readable name
/// - An icon
const CATEGORY_TO_METADATA = {
    document: ['Documents', 'material/description'],
    picture: ['Pictures', 'material/landscape:fill'],
    data: ['Data files', 'material/pie_chart'],
};

type UploadAreaState = ComponentState & {
    _type_: 'UploadArea-builtin';
    content?: string;
    file_types?: string[];
};

export class UploadAreaComponent extends ComponentBase {
    state: Required<UploadAreaState>;

    private fileInput: HTMLInputElement;
    private iconElement: HTMLElement;
    private childContainer: HTMLElement;
    private titleElement: HTMLElement;
    private fileTypesElement: HTMLElement;
    private progressElement: HTMLElement;

    private rippleInstance: RippleEffect;

    createElement(): HTMLElement {
        // Create the element
        let element = document.createElement('div');
        element.classList.add('rio-upload-area');

        // Create the icon element but don't add it
        this.iconElement = document.createElement('div');
        this.iconElement.classList.add('rio-upload-area-icon');

        // Create the child container
        this.childContainer = document.createElement('div');
        this.childContainer.classList.add('rio-upload-area-child-container');
        element.appendChild(this.childContainer);

        // Create the title element, but don't add it
        this.titleElement = document.createElement('div');
        this.titleElement.classList.add('rio-upload-area-title');

        // Same for the file types element
        this.fileTypesElement = document.createElement('div');
        this.fileTypesElement.classList.add('rio-upload-area-file-types');

        // Create the progress element
        this.progressElement = document.createElement('div');
        this.progressElement.classList.add('rio-upload-area-progress-bar');
        element.appendChild(this.progressElement);

        // A hidden file input
        this.fileInput = document.createElement('input');
        this.fileInput.type = 'file';
        this.fileInput.multiple = true;
        element.appendChild(this.fileInput);

        // Add a material ripple effect
        this.rippleInstance = new RippleEffect(element, {
            triggerOnPress: false,
        });

        // Populate the child container with the default content
        this.createDefaultContent();

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
            const files = e.target.files;
            this.uploadFiles(files);
        });

        return element;
    }

    updateElement(
        deltaState: UploadAreaState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        // Title
        if (deltaState.content !== undefined) {
            this.titleElement.textContent = deltaState.content;
        }

        // File types
        if (deltaState.file_types !== undefined) {
            // Update the UI
            this.updateFileTypes(deltaState.file_types);

            // Update the file input
            this.fileInput.type = 'file';
            this.fileInput.accept = deltaState.file_types
                .map((x) => `.${x}`)
                .join(',');

            this.fileInput.style.display = 'none';
        }
    }

    /// Updates the text & icon for the file types
    updateFileTypes(fileTypes: string[] | null): void {
        // Start off generic
        let fileTypesText: string = 'All files supported';
        let icon: string = 'material/upload';

        // Are there a nicer text & icon to display?
        if (fileTypes !== null) {
            // What sort of files types are we dealing with?
            let fileCategories = new Set<string>();

            for (const fileType of fileTypes) {
                if (fileType in EXTENSION_TO_CATEGORY) {
                    fileCategories.add(EXTENSION_TO_CATEGORY[fileType]);
                } else {
                    fileCategories.clear();
                    break;
                }
            }

            // Is there a single type?
            if (fileCategories.size === 1) {
                const category = fileCategories.values().next().value;
                const [newText, newIcon] = CATEGORY_TO_METADATA[category];

                if (fileTypes.length === 1) {
                    fileTypesText = `${fileTypes[0].toUpperCase()} ${newText}`;
                } else {
                    let extensionText = fileTypes
                        .map((x) => `*.${x}`)
                        .join(', ');
                    fileTypesText = `${newText} (${extensionText})`;
                }

                icon = newIcon;
            }
            // Nope, but we can list the extensions
            else {
                fileTypesText = fileTypes.map((x) => `*.${x}`).join(', ');
            }
        }

        // Apply the values
        applyIcon(this.iconElement, icon, 'currentColor');
        this.fileTypesElement.textContent = fileTypesText;
    }

    /// Populates the child container with the default content
    createDefaultContent(): void {
        // Icon
        this.childContainer.appendChild(this.iconElement);

        // Column for the title and file types
        let column = document.createElement('div');
        column.classList.add('rio-upload-area-column');
        this.childContainer.appendChild(column);

        // Title
        column.appendChild(this.titleElement);

        // File types
        column.appendChild(this.fileTypesElement);

        // Button
        //
        // The structure below is more complicated than strictly necessary. This
        // is done to emulate the HTML of a regular `rio.Button`, so the
        // existing button styles can be used.
        //
        // Note that the button needs to event handler at all. The file input
        // already handles click events as intended. The button merely serves
        // as visual indicator that the area is clickable.
        let buttonOuter = document.createElement('div');
        buttonOuter.classList.add(
            'rio-upload-area-button',
            'rio-button',
            'rio-shape-rounded'
        );
        this.childContainer.appendChild(buttonOuter);

        let buttonInner = document.createElement('div');
        buttonInner.classList.add(
            'rio-switcheroo-bump',
            'rio-buttonstyle-major'
        );
        buttonOuter.appendChild(buttonInner);
        buttonInner.textContent = 'Browse';
    }

    uploadFiles(files: FileList): void {
        // Build a `FormData` object containing the files
        const data = new FormData();

        let ii = 0;
        for (const file of files || []) {
            ii += 1;
            data.append('file_names', file.name);
            data.append('file_types', file.type);
            data.append('file_sizes', file.size.toString());
            data.append('file_streams', file, file.name);
        }

        // FastAPI has trouble parsing empty form data. Append a dummy value so
        // it's never empty
        data.append('dummy', 'dummy');

        // Upload the files
        const xhr = new XMLHttpRequest();
        const url = `${globalThis.RIO_BASE_URL}rio/upload-to-component/${globalThis.SESSION_TOKEN}/${this.id}`;

        xhr.open('PUT', url, true);

        xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
                const progress = event.loaded / event.total;

                this.progressElement.style.opacity = '1';
                this.progressElement.style.setProperty(
                    '--progress',
                    `${progress * 100}%`
                );
            }
        };

        xhr.onload = () => {
            this.progressElement.style.opacity = '0';
        };

        xhr.onerror = () => {
            this.progressElement.style.opacity = '0';
        };

        xhr.send(data);
    }
}
