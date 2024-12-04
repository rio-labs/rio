import { getComponentLayout } from "./utils";
import { pixelsPerRem } from "./app";
import {
    componentsById,
    getRootComponent,
    recursivelyDeleteComponent,
} from "./componentManagement";
import { ComponentBase } from "./components/componentBase";
import {
    ComponentLayout,
    UnittestClientLayoutInfo,
    UnittestComponentLayout,
} from "./dataModels";
import { applyIcon } from "./designApplication";
import { markEventAsHandled, stopPropagation } from "./eventHandling";
import {
    buildUploadFormData,
    createBrowseButton,
} from "./components/filePickerArea";
import { RippleEffect } from "./rippleEffect";

export async function registerFont(
    name: string,
    urls: (string | null)[]
): Promise<void> {
    const VARIATIONS = [
        { weight: "normal", style: "normal" },
        { weight: "bold", style: "normal" },
        { weight: "normal", style: "italic" },
        { weight: "bold", style: "italic" },
    ];

    let fontFaces = new Map<string, FontFace>();

    for (let [i, url] of urls.entries()) {
        if (url === null) {
            continue;
        }

        // There is/was a bug in Firefox where `FontFace.load()` hangs
        // indefinitely if the FontFace is garbage collected. So make sure to
        // keep a reference to the FontFace at all times.
        let fontFace = new FontFace(name, `url(${url})`, VARIATIONS[i]);
        fontFace.load();

        fontFaces.set(url, fontFace);
    }

    let numSuccesses = 0;
    let numFailures = 0;

    for (let [url, fontFace] of fontFaces.entries()) {
        try {
            await fontFace.loaded;
        } catch (error) {
            numFailures++;
            console.warn(`Failed to load font file ${url}: ${error}`);
            continue;
        }

        numSuccesses++;
        document.fonts.add(fontFace);
    }

    if (numFailures === 0) {
        console.debug(
            `Successfully registered all ${numSuccesses} variations of font ${name}`
        );
    } else if (numSuccesses === 0) {
        console.warn(
            `Failed to register all ${numFailures} variations of font ${name}`
        );
    } else {
        console.warn(
            `Successfully registered ${numSuccesses} variations of font ${name}, but failed to register ${numFailures} variations`
        );
    }
}

export function requestFileUpload(message: any): void {
    // Some browsers refuse to let us open a file upload dialog
    // programmatically. And since there's no reliable way to detect whether
    // that's the case, we'll play it safe and both display a dialog AND a
    // fallback picker.
    //
    // Build the fallback UI
    let dialog = document.createElement("div");
    dialog.classList.add("request-file-upload-fallback-dialog");

    let closeButton = document.createElement("div");
    dialog.appendChild(closeButton);
    closeButton.classList.add(
        "request-file-upload-fallback-dialog-close-button"
    );
    applyIcon(closeButton, "material/close", "currentColor");
    closeButton.addEventListener("click", (event: Event) => {
        onFinish();
        markEventAsHandled(event);
    });

    let column = document.createElement("div");
    dialog.appendChild(column);
    column.classList.add("request-file-upload-fallback-dialog-column");

    let icon = document.createElement("div");
    column.appendChild(icon);
    icon.classList.add("request-file-upload-fallback-dialog-upload-icon");
    applyIcon(icon, "material/upload", "currentColor");

    let span = document.createElement("span");
    column.appendChild(span);
    span.textContent = "Drag & Drop files here";

    // File upload input element
    let input = document.createElement("input");
    column.appendChild(input);
    input.type = "file";
    input.multiple = message.multiple;

    if (message.fileTypes !== null) {
        input.accept = message.fileTypes.map((x) => `.${x}`).join(",");
    }

    input.addEventListener("change", () => onFinish());
    input.addEventListener("cancel", () => onFinish(null));

    // Browse button
    let button = createBrowseButton("primary");
    column.appendChild(button);

    // Make the entire dialog clickable. To prevent recursion, we must also
    // stop the click event from propagating upwards if the input was clicked.
    dialog.addEventListener("click", () => {
        input.click();
    });
    input.addEventListener("click", stopPropagation);

    // Close the dialog on Esc press
    function onKeyDown(event: KeyboardEvent) {
        if (event.key !== "Escape") {
            return;
        }

        onFinish();
        markEventAsHandled(event);
        document.removeEventListener("keydown", onKeyDown);
    }
    document.addEventListener("keydown", onKeyDown);

    // Enable drag-n-drop
    //
    // Highlight drop area when dragging files over it
    dialog.addEventListener("dragenter", (event: DragEvent) => {
        dialog.classList.add("dragging");
        markEventAsHandled(event);
    });
    dialog.addEventListener("dragleave", (event: DragEvent) => {
        dialog.classList.remove("dragging");
        markEventAsHandled(event);
    });

    // Listening to `dragover` is required for drag-n-drop to work. Sigh.
    dialog.addEventListener("dragover", (event: Event) => {
        // The `dragleave` event triggers when hovering over a child element,
        // which is dumb. So we use this event to re-add the relevant style
        // every time the mouse moves.
        dialog.classList.add("dragging");
        markEventAsHandled(event);
    });

    dialog.addEventListener("drop", (event: DragEvent) => {
        // Why can this be null?
        if (event.dataTransfer == null) {
            return;
        }

        markEventAsHandled(event);

        // Upload the file(s)
        const files = event.dataTransfer.files;
        onFinish(files);
    });

    // Prevent scrolling while the dialog is open
    document.body.style.overflow = "hidden";

    // Add the dialog to the DOM
    document.querySelector(".rio-overlays-container")!.appendChild(dialog);

    // This code runs when the dialog is closed, whether a file was selected or
    // not
    function onFinish(files?: FileList | null) {
        // Don't run twice. This can potentially happen if the opened dialog
        // isn't modal, which would allow the user to click our custom dialog's
        // "close" button.
        if (dialog.parentElement === null) {
            return;
        }

        // If no files were passed in, get the files from the input element
        if (files === undefined) {
            files = input.files;
        }

        // Build a `FormData` object containing the files
        const data = buildUploadFormData(files);

        // Upload the files
        fetch(message.uploadUrl, {
            method: "PUT",
            body: data,
        });

        // Re-enable scrolling
        document.body.style.removeProperty("overflow");

        // Remove the input element from the DOM. Removing this too early causes
        // weird behavior in some browsers.
        dialog.remove();
    }

    // Try to programmatically open the file upload dialog
    input.click();
}

export function setTitle(title: string): void {
    document.title = title;
}

export function closeSession(): void {
    console.trace("closeSession was called somehow! This shouldn't happen!");
    // window.close(); // TODO: What if the browser doesn't allow this?
}

/// Gathers layout information for the given components.
export function getComponentLayouts(
    componentIds: number[]
): (ComponentLayout | null)[] {
    let result: (ComponentLayout | null)[] = [];

    for (let componentId of componentIds) {
        {
            // Find the component
            let component: ComponentBase = componentsById[componentId];

            if (component === undefined) {
                result.push(null);
                continue;
            }

            // Fetch layout information
            result.push(getComponentLayout(component));
        }
    }

    return result;
}

function dumpComponentRecursively(
    component: ComponentBase,
    componentLayouts: { [componentId: number]: UnittestComponentLayout }
) {
    // Prepare the layout
    let subresult = getComponentLayout(component) as UnittestComponentLayout;

    // Add properties specific to unittests
    subresult.aux = {};

    // Save the layout
    componentLayouts[component.id] = subresult;

    // Recurse to children
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

export function removeDialog(rootComponentId: number): void {
    // Get the dialog's root component
    let rootComponent = componentsById[rootComponentId];

    // Because of network latency, the component might have been removed already
    if (rootComponent === undefined) {
        return;
    }

    // Let the dialog handle the removal
    recursivelyDeleteComponent(rootComponent);
}
