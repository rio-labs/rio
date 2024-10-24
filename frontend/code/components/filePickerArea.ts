import { applyIcon, applySwitcheroo } from "../designApplication";
import { ComponentBase, ComponentState } from "./componentBase";
import { RippleEffect } from "../rippleEffect";

/// Maps MIME types to what sort of file they represent
const EXTENSION_TO_CATEGORY = {
    aac: "audio",
    avi: "video",
    bat: "code",
    bmp: "picture",
    c: "code",
    cpp: "code",
    cs: "code",
    css: "code",
    csv: "data",
    doc: "document",
    docx: "document",
    flac: "audio",
    gif: "picture",
    go: "code",
    h: "code",
    h5: "data",
    hdf5: "data",
    hpp: "code",
    html: "code",
    ini: "data",
    java: "code",
    jpg: "picture",
    js: "code",
    json: "data",
    jxl: "picture",
    kt: "code",
    lua: "code",
    md: "document",
    mkv: "video",
    mov: "video",
    mp3: "audio",
    mp4: "video",
    ods: "data",
    odt: "document",
    oga: "audio",
    parquet: "data",
    pdf: "document",
    php: "code",
    pickle: "data",
    pkl: "data",
    png: "picture",
    pptx: "document",
    py: "code",
    r: "code",
    rs: "code",
    sh: "code",
    sql: "code",
    svg: "picture",
    toml: "data",
    ts: "code",
    tsv: "data",
    txt: "document",
    wav: "audio",
    webp: "picture",
    wmv: "video",
    xlsx: "data",
    xml: "code",
    yaml: "data",
    yml: "data",
};

/// Maps types of files to
///
/// - A human-readable name
/// - An icon
const CATEGORY_TO_METADATA = {
    audio: ["audio files", "material/music_note"],
    code: ["code files", "material/code"],
    data: ["data files", "material/pie_chart"],
    document: ["documents", "material/description"],
    media: ["media files", "material/music_note"],
    picture: ["pictures", "material/landscape:fill"],
    video: ["videos", "material/movie"],
};

type FilePickerAreaState = ComponentState & {
    _type_: "FilePickerArea-builtin";
    content?: string | null;
    file_types?: string[];
};

export class FilePickerAreaComponent extends ComponentBase {
    declare state: Required<FilePickerAreaState>;

    private fileInput: HTMLInputElement;
    private iconElement: HTMLElement;
    private childContainer: HTMLElement;
    private titleElement: HTMLElement;
    private fileTypesElement: HTMLElement;
    private progressElement: HTMLElement;

    private rippleInstance: RippleEffect /*  */;

    createElement(): HTMLElement {
        // Create the element
        let element = document.createElement("div");
        element.classList.add("rio-file-picker-area");

        // Create the icon element but don't add it
        this.iconElement = document.createElement("div");
        this.iconElement.classList.add("rio-file-picker-area-icon");

        // Create the child container
        this.childContainer = document.createElement("div");
        this.childContainer.classList.add(
            "rio-file-picker-area-child-container"
        );
        element.appendChild(this.childContainer);

        // Create the progress element
        this.progressElement = document.createElement("div");
        this.progressElement.classList.add("rio-file-picker-area-progress");
        element.appendChild(this.progressElement);

        // Create the title element, but don't add it
        this.titleElement = document.createElement("div");
        this.titleElement.classList.add("rio-file-picker-area-title");

        // Same for the file types element
        this.fileTypesElement = document.createElement("div");
        this.fileTypesElement.classList.add("rio-file-picker-area-file-types");

        // A hidden file input
        this.fileInput = document.createElement("input");
        this.fileInput.type = "file";
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
        ["dragenter", "dragover"].forEach((eventName) => {
            element.addEventListener(
                eventName,
                (event) => {
                    event.preventDefault();
                    event.stopPropagation();

                    const dragEvent = event as DragEvent;
                    const rect = element.getBoundingClientRect();
                    const x = dragEvent.clientX - rect.left;
                    const y = dragEvent.clientY - rect.top;

                    element.style.setProperty("--x", `${x}px`);
                    element.style.setProperty("--y", `${y}px`);
                    element.classList.add("rio-file-picker-area-file-hover");
                },
                false
            );
        });

        ["dragleave", "drop"].forEach((eventName) => {
            element.addEventListener(
                eventName,
                (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    element.classList.remove("rio-file-picker-area-file-hover");
                },
                false
            );
        });

        // Handle dropped files
        element.addEventListener(
            "drop",
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

        // Open file picker when clicking the drop area
        element.addEventListener("click", () => {
            this.fileInput.click();
        });

        // Handle files selected from the file input
        this.fileInput.addEventListener("change", (e) => {
            // @ts-ignore
            this.uploadFiles(e.target.files);
        });

        return element;
    }

    updateElement(
        deltaState: FilePickerAreaState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        // Title
        if (deltaState.content !== undefined) {
            this.titleElement.textContent =
                deltaState.content === null
                    ? "Drag & Drop files here"
                    : deltaState.content;
        }

        // File types
        if (deltaState.file_types !== undefined) {
            // Update the UI
            this.updateFileTypes(deltaState.file_types);

            // Update the file input
            this.fileInput.type = "file";

            if (deltaState.file_types === null) {
                this.fileInput.accept = "";
            } else {
                this.fileInput.accept = deltaState.file_types
                    .map((x) => `.${x}`)
                    .join(",");
            }
        }
    }

    /// Updates the text & icon for the file types
    updateFileTypes(fileTypes: string[] | null): void {
        // Start off generic
        let fileTypesText: string = "All files supported";
        let icon: string = "material/folder";

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

            // Special cases: If both audio and video files are present, treat
            // them as media files
            if (fileCategories.has("audio") && fileCategories.has("video")) {
                fileCategories.delete("audio");
                fileCategories.delete("video");
                fileCategories.add("media");
            }

            // Are we looking for a single category?
            if (fileCategories.size === 1) {
                const category = fileCategories.values().next().value;
                const [newText, newIcon] = CATEGORY_TO_METADATA[category];

                if (fileTypes.length === 1) {
                    fileTypesText = `${fileTypes[0].toUpperCase()} ${newText}`;
                } else {
                    let extensionText = fileTypes
                        .map((x) => `*.${x}`)
                        .join(" ");

                    let newTextCapitalized =
                        newText.charAt(0).toUpperCase() + newText.slice(1);

                    fileTypesText = `${newTextCapitalized} (${extensionText})`;
                }

                icon = newIcon;
            }
            // Nope, but we can list the extensions
            else if (fileTypes.length > 0) {
                fileTypesText = fileTypes.map((x) => `*.${x}`).join(" ");
            }
        }

        // Apply the values
        applyIcon(this.iconElement, icon, "currentColor");
        this.fileTypesElement.textContent = fileTypesText;
    }

    /// Populates the child container with the default content
    createDefaultContent(): void {
        // Icon
        this.childContainer.appendChild(this.iconElement);

        // Column for the title and file types
        let column = document.createElement("div");
        column.classList.add("rio-file-picker-area-column");
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
        let buttonOuter = document.createElement("div");
        buttonOuter.classList.add(
            "rio-file-picker-area-button",
            "rio-button",
            "rio-shape-rounded"
        );
        this.childContainer.appendChild(buttonOuter);

        let buttonInner = document.createElement("div");
        buttonInner.classList.add(
            "rio-switcheroo-bump",
            "rio-buttonstyle-major"
        );
        buttonOuter.appendChild(buttonInner);
        buttonInner.textContent = "Browse";
    }

    uploadFiles(files: FileList): void {
        // Build a `FormData` object containing the files
        const data = new FormData();

        let ii = 0;
        for (const file of files || []) {
            ii += 1;
            data.append("file_names", file.name);
            data.append("file_types", file.type);
            data.append("file_sizes", file.size.toString());
            data.append("file_streams", file, file.name);
        }

        // FastAPI has trouble parsing empty form data. Append a dummy value so
        // it's never empty
        data.append("dummy", "dummy");

        // Upload the files
        const xhr = new XMLHttpRequest();
        const url = `${globalThis.RIO_BASE_URL}rio/upload-to-component/${globalThis.SESSION_TOKEN}/${this.id}`;

        xhr.open("PUT", url, true);

        xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
                const progress = event.loaded / event.total;

                this.progressElement.style.opacity = "0.2";
                this.progressElement.style.width = `${progress * 100}%`;
            }
        };

        xhr.onload = () => {
            this.progressElement.style.opacity = "0";
        };

        xhr.onerror = () => {
            this.progressElement.style.opacity = "0";
        };

        xhr.send(data);
    }
}
