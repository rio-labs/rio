import { applyIcon, applySwitcheroo } from "../designApplication";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { RippleEffect } from "../rippleEffect";
import { markEventAsHandled } from "../eventHandling";
import { ColorSetName, ComponentId } from "../dataModels";
import { ComponentStatesUpdateContext } from "../componentManagement";

/// Maps MIME types to what sort of file they represent
const EXTENSION_TO_CATEGORY = {
    "7z": "archive",
    "tar.bz2": "archive",
    "tar.gz": "archive",
    "tar.lz4": "archive",
    "tar.xz": "archive",
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
    tar: "archive",
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
    zip: "archive",
};

/// Maps types of files to
///
/// - A human-readable name
/// - An icon
const CATEGORY_TO_METADATA = {
    archive: ["archives", "material/folder_zip"],
    audio: ["audio files", "material/music_note"],
    code: ["code files", "material/code"],
    data: ["data files", "material/pie_chart"],
    document: ["documents", "material/description"],
    media: ["media files", "material/music_note"],
    picture: ["pictures", "material/landscape:fill"],
    video: ["videos", "material/movie"],
};

/// Given a filename, return the icon to use for it
function getFileIcon(filename: string): string {
    // If the file name starts with a dot its a hidden file, not a suffix
    if (filename.startsWith(".")) {
        filename = filename.slice(1);
    }

    // Get the file suffix, if there is one
    const parts = filename.split(".");
    const suffix = parts.length > 1 ? parts.slice(1).join(".") : "";

    // Get the category this file is in
    const category = EXTENSION_TO_CATEGORY[suffix];

    // Get the icon for this category
    if (category === undefined) {
        return "material/description";
    } else {
        return CATEGORY_TO_METADATA[category][1];
    }
}

type FilePickerAreaState = ComponentState & {
    _type_: "FilePickerArea-builtin";
    child_text: string | null;
    child_component: ComponentId | null;
    file_types: string[];
    multiple: boolean;
    files: {
        id: string;
        name: string;
    }[];
};

export class FilePickerAreaComponent extends ComponentBase<FilePickerAreaState> {
    private fileInput: HTMLInputElement;
    private iconElement: HTMLElement;
    private childContentContainer: HTMLElement;
    private defaultContentContainer: HTMLElement;
    private titleElement: HTMLElement;
    private fileTypesElement: HTMLElement;
    private progressElement: HTMLElement;
    private filesElement: HTMLElement;

    private rippleInstance: RippleEffect;

    // Used to keep track of upload progress. Each upload generates a unique
    // ID and then stores its current progress and total size here.
    //
    // The first value in the map is the number of bytes uploaded so far, the
    // second value is the total number of bytes to upload, and the third value
    // is a boolean indicating whether the upload has finished.
    private nextFreeUploadId: number = 0;
    private uploadProgresses: Map<number, [number, number, boolean]> =
        new Map();

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        // Create the element
        let element = document.createElement("div");
        element.classList.add("rio-file-picker-area");

        // Create a container to hold the changing content
        this.childContentContainer = document.createElement("div");
        this.childContentContainer.classList.add(
            "rio-file-picker-area-child-content-container"
        );
        element.appendChild(this.childContentContainer);

        // Create a single container for all of the default content. This allows
        // easy switching between custom & default content.
        //
        // This element will be added later, if no custom content was provided.
        this.defaultContentContainer = document.createElement("div");
        this.defaultContentContainer.classList.add(
            "rio-file-picker-area-default-content-container"
        );

        // Header element
        let headerElement = document.createElement("div");
        headerElement.classList.add("rio-file-picker-area-header");
        this.defaultContentContainer.appendChild(headerElement);

        // Large Icon
        this.iconElement = document.createElement("div");
        this.iconElement.classList.add("rio-file-picker-area-icon");
        headerElement.appendChild(this.iconElement);

        // Column for title & file types
        let textColumn = document.createElement("div");
        textColumn.classList.add("rio-file-picker-area-text-column");
        headerElement.appendChild(textColumn);

        // Create the title element
        this.titleElement = document.createElement("div");
        this.titleElement.classList.add("rio-file-picker-area-title");
        textColumn.appendChild(this.titleElement);

        // Create the file types element
        this.fileTypesElement = document.createElement("div");
        this.fileTypesElement.classList.add("rio-file-picker-area-file-types");
        textColumn.appendChild(this.fileTypesElement);

        // Browse Button
        let button = createBrowseButton("keep");
        button.classList.add("rio-file-picker-area-button");
        headerElement.appendChild(button);

        // Create the files element
        this.filesElement = document.createElement("div");
        this.filesElement.classList.add("rio-file-picker-area-files");
        this.defaultContentContainer.appendChild(this.filesElement);

        // Create the progress element
        this.progressElement = document.createElement("div");
        this.progressElement.classList.add("rio-file-picker-area-progress");
        element.appendChild(this.progressElement);

        // A hidden file input
        this.fileInput = document.createElement("input");
        this.fileInput.type = "file";
        this.fileInput.multiple = true;
        element.appendChild(this.fileInput);

        // A material ripple effect
        this.rippleInstance = new RippleEffect(element, {
            triggerOnPress: false,
        });

        // Connect event handlers
        //
        // Highlight drop area when dragging files over it
        ["dragenter", "dragover"].forEach((eventName) => {
            element.addEventListener(eventName, (event) => {
                markEventAsHandled(event);

                const dragEvent = event as DragEvent;
                const rect = element.getBoundingClientRect();
                const x = dragEvent.clientX - rect.left;
                const y = dragEvent.clientY - rect.top;

                element.style.setProperty("--x", `${x}px`);
                element.style.setProperty("--y", `${y}px`);
                element.classList.add("rio-file-picker-area-file-hover");
            });
        });

        ["dragleave", "drop"].forEach((eventName) => {
            element.addEventListener(eventName, (event) => {
                // Important: Don't call `stopImmediatePropagation()` because
                // then the other `drag` handler below won't run.
                event.preventDefault();
                event.stopPropagation();

                element.classList.remove("rio-file-picker-area-file-hover");
            });
        });

        // Handle dropped files
        element.addEventListener("drop", (event: DragEvent) => {
            // Why can this be null?
            if (event.dataTransfer == null) {
                return;
            }

            // Trigger the ripple effect
            this.rippleInstance.trigger(event);

            // Upload the file(s)
            const files = event.dataTransfer.files;
            this.uploadFiles(files);
        });

        // Open file picker when clicking the drop area
        element.addEventListener("click", () => {
            // If running in a window, let Python handle the file picking. This
            // way no file needs to be sent to the server.
            if (globalThis.RUNNING_IN_WINDOW) {
                this.sendMessageToBackend({
                    type: "pickFile",
                });
            } else {
                this.fileInput.click();
            }
        });

        // Handle files selected from the file input
        this.fileInput.addEventListener("change", (e) => {
            this.uploadFiles((e.target as HTMLInputElement).files);
        });

        return element;
    }

    updateElement(
        deltaState: DeltaState<FilePickerAreaState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        // If custom content was provided, use it
        if (
            deltaState.child_component !== undefined &&
            deltaState.child_component !== null
        ) {
            this.removeHtmlOrComponentChildren(
                context,
                this.childContentContainer
            );
            this.replaceOnlyChild(
                context,
                deltaState.child_component,
                this.childContentContainer
            );
        }

        // If the default content is requested, add that
        if (
            deltaState.child_text !== undefined &&
            deltaState.child_component === null
        ) {
            this.removeHtmlOrComponentChildren(
                context,
                this.childContentContainer
            );
            this.childContentContainer.appendChild(
                this.defaultContentContainer
            );

            this.titleElement.textContent =
                deltaState.child_text === null
                    ? "Drag & Drop files here"
                    : deltaState.child_text;
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

        // Multiple files?
        if (deltaState.multiple !== undefined) {
            this.fileInput.multiple = deltaState.multiple;
        }

        // Already picked files
        if (deltaState.files !== undefined) {
            this.state.files = deltaState.files;
            this.updatePickedFileElements();
        }
    }

    /// Updates the list of picked files
    updatePickedFileElements(): void {
        // Clear the list
        this.filesElement.innerHTML = "";

        // Add the new files
        for (const file of this.state.files) {
            let fileElement = document.createElement("div");
            fileElement.classList.add("rio-file-picker-area-file");

            let iconElement = document.createElement("div");
            iconElement.classList.add("rio-file-picker-area-file-icon");
            applyIcon(iconElement, getFileIcon(file.name), "currentColor");
            fileElement.appendChild(iconElement);

            let nameElement = document.createElement("div");
            nameElement.classList.add("rio-file-picker-area-file-name");
            nameElement.textContent = file.name;
            fileElement.appendChild(nameElement);

            let removeElement = document.createElement("div");
            removeElement.classList.add("rio-file-picker-area-file-remove");
            applyIcon(removeElement, "material/close", "currentColor");
            fileElement.appendChild(removeElement);

            // Listen for events
            fileElement.addEventListener("click", markEventAsHandled);

            removeElement.addEventListener("click", (event) => {
                markEventAsHandled(event);

                this.sendMessageToBackend({
                    type: "removeFile",
                    fileId: file.id,
                });
            });

            this.filesElement.appendChild(fileElement);
        }
    }

    /// Updates the text & icon for the file types
    updateFileTypes(fileTypes: string[] | null): void {
        // Start off generic
        let fileTypesText: string = "All file types";
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

    uploadFiles(files: FileList | null): void {
        // Build a unique ID for this upload
        const uploadId = this.nextFreeUploadId;
        this.nextFreeUploadId += 1;

        // Build a `FormData` object containing the files
        const data = buildUploadFormData(files);

        // Upload the files
        const xhr = new XMLHttpRequest();
        const url = `${globalThis.RIO_BASE_URL}rio/upload-to-component?session_token=${globalThis.SESSION_TOKEN}&component_id=${this.id}`;

        xhr.open("PUT", url, true);

        // Keep updating the progress bar
        let setFinished = (event: ProgressEvent) => {
            let oldEntry = this.uploadProgresses.get(uploadId);

            if (oldEntry === undefined) {
                this.uploadProgresses.set(uploadId, [
                    event.loaded,
                    event.total,
                    true,
                ]);
            } else {
                oldEntry[2] = true;
            }

            this.updateProgressDisplay();
        };

        xhr.onload = setFinished;
        xhr.onerror = setFinished;

        xhr.upload.onprogress = (event) => {
            this.uploadProgresses.set(uploadId, [
                event.loaded,
                event.total,
                false,
            ]);
            this.updateProgressDisplay();
        };

        xhr.send(data);
    }

    updateProgressDisplay(): void {
        // Special case: No uploads in progress
        if (this.uploadProgresses.size === 0) {
            this.progressElement.style.opacity = "0";
            return;
        }

        // Get the current progress and total number of bytes
        let currentBytes = 0;
        let totalBytes = 0;
        let allDownloadsFinished = true;

        for (const [_, [current, total, finished]] of this.uploadProgresses) {
            currentBytes += current;
            totalBytes += total;

            allDownloadsFinished = allDownloadsFinished && finished;
        }

        // If all downloads have finished, clear the progress bar. If uploads
        // would remove themselves the second they finish, the progress fraction
        // would drop, which is confusing.
        if (allDownloadsFinished) {
            this.uploadProgresses.clear();
            this.progressElement.style.opacity = "0";
            return;
        }

        // Update the progress bar
        let progressFraction = totalBytes === 0 ? 0 : currentBytes / totalBytes;

        this.progressElement.style.opacity = "0.2";
        this.progressElement.style.width = `${progressFraction * 100}%`;
    }
}

// The code below is also used by the RPC function "requestFileUpload"

export function createBrowseButton(colorSet: ColorSetName): HTMLElement {
    // The structure below is more complicated than strictly necessary. This
    // is done to emulate the HTML of a regular `rio.Button`, so the
    // existing button styles can be used.
    //
    // Note that the button needs no event handler at all. The file input
    // already handles click events as intended. The button merely serves
    // as visual indicator that the area is clickable.
    let buttonOuter = document.createElement("div");
    buttonOuter.classList.add(
        "rio-button",
        "rio-shape-rounded",
        "rio-upload-file-button"
    );

    let buttonInner = document.createElement("div");
    buttonInner.classList.add("rio-buttonstyle-major");
    applySwitcheroo(buttonInner, colorSet === "keep" ? "bump" : colorSet);

    buttonOuter.appendChild(buttonInner);
    buttonInner.textContent = "Browse";

    return buttonOuter;
}

export function buildUploadFormData(files: FileList | null): FormData {
    const data = new FormData();

    for (const file of files || []) {
        data.append("files", file, file.name);
    }

    return data;
}
