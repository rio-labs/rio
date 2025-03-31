import { getComponentLayout, scrollToUrlFragment, sleep } from "./utils";
import { pixelsPerRem } from "./app";
import {
    componentsById,
    getRootComponent,
    recursivelyDeleteComponent,
} from "./componentManagement";
import { ComponentBase } from "./components/componentBase";
import {
    ComponentId,
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
import { PopupManager } from "./popupManager";
import { setConnectionLostPopupVisibleUnlessGoingAway } from "./rpc";
import { FullscreenPositioner } from "./popupPositioners";

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
    let fallbackRoot = document.createElement("div");
    fallbackRoot.classList.add("request-file-upload-fallback-dialog");

    let closeButton = document.createElement("div");
    fallbackRoot.appendChild(closeButton);
    closeButton.classList.add(
        "request-file-upload-fallback-dialog-close-button"
    );
    applyIcon(closeButton, "material/close", "currentColor");
    closeButton.addEventListener("click", (event: Event) => {
        onFinish();
        markEventAsHandled(event);
    });

    let column = document.createElement("div");
    fallbackRoot.appendChild(column);
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

    if (message.file_types !== null) {
        input.accept = message.file_types.map((x) => `.${x}`).join(",");
    }

    input.addEventListener("change", () => onFinish());
    input.addEventListener("cancel", () => onFinish(null));

    // Browse button
    let button = createBrowseButton("primary");
    column.appendChild(button);

    // Make the entire dialog clickable. To prevent recursion, we must also
    // stop the click event from propagating upwards if the input was clicked.
    fallbackRoot.addEventListener("click", () => {
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
    }
    document.addEventListener("keydown", onKeyDown);

    // Enable drag-n-drop
    //
    // Highlight drop area when dragging files over it
    fallbackRoot.addEventListener("dragenter", (event: DragEvent) => {
        fallbackRoot.classList.add("dragging");
        markEventAsHandled(event);
    });
    fallbackRoot.addEventListener("dragleave", (event: DragEvent) => {
        fallbackRoot.classList.remove("dragging");
        markEventAsHandled(event);
    });

    // Listening to `dragover` is required for drag-n-drop to work. Sigh.
    fallbackRoot.addEventListener("dragover", (event: Event) => {
        // The `dragleave` event triggers when hovering over a child element,
        // which is dumb. So we use this event to re-add the relevant style
        // every time the mouse moves.
        fallbackRoot.classList.add("dragging");
        markEventAsHandled(event);
    });

    fallbackRoot.addEventListener("drop", (event: DragEvent) => {
        // Why can this be null?
        if (event.dataTransfer == null) {
            return;
        }

        markEventAsHandled(event);

        // Upload the file(s)
        onFinish(event.dataTransfer.files);
    });

    // Prevent scrolling while the dialog is open
    document.body.style.overflow = "hidden";

    // This code runs when the dialog is closed, whether a file was selected or
    // not
    let finishHasRun = false;

    function onFinish(files?: FileList | null) {
        // Don't run twice. This can potentially happen if the opened dialog
        // isn't modal, which would allow the user to click our custom dialog's
        // "close" button.
        if (finishHasRun) {
            return;
        }
        finishHasRun = true;

        // If no files were passed in, get the files from the input element
        if (files === undefined) {
            files = input.files;
        }

        // Build a `FormData` object containing the files
        const data = buildUploadFormData(files);

        // Upload the files
        fetch(message.upload_url, {
            method: "PUT",
            body: data,
        });

        // Re-enable scrolling
        document.body.style.removeProperty("overflow");

        // Only now clean up. Removing the input element too early causes issues
        // in some browsers.
        popupManager.destroy();
        document.removeEventListener("keydown", onKeyDown);
    }

    // Display the fallback

    // Pick an arbitrary element as the anchor. It's only used to determine the
    // correct overlays-container.
    let anchor = componentsById[getRootComponent().state.content]!.element;
    let popupManager = new PopupManager({
        anchor: anchor,
        content: fallbackRoot,
        positioner: new FullscreenPositioner(),
        // While the dialog is modal, it darkens the background more than the
        // popup manager might. Hence turn off the manager's feature - we'll
        // darken and block events ourselves.
        modal: false,
        userClosable: false,
    });

    popupManager.isOpen = true;

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
    componentIds: ComponentId[]
): (ComponentLayout | null)[] {
    let result: (ComponentLayout | null)[] = [];

    for (let componentId of componentIds) {
        {
            // Find the component
            let component = componentsById[componentId];

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

export async function getUnittestClientLayoutInfo(): Promise<UnittestClientLayoutInfo> {
    // This function is only used by rio's unit tests. We know it runs after the
    // first `updateComponentStates`, so we don't need to worry about that. But,
    // since layouting includes quite a few `requestAnimationFrame`s and
    // `resizeObserver`s, some layouts may still be in flux. We'll wait a little
    // while before we fetch the layouts.
    await sleep(0.1);

    // Prepare the result
    const result = {} as UnittestClientLayoutInfo;

    result.windowWidth = window.innerWidth / pixelsPerRem;
    result.windowHeight = window.innerHeight / pixelsPerRem;

    result.componentLayouts = {};

    // Dump recursively, starting with the root component
    let rootComponent = getRootComponent();

    // Invisible elements produce a size of (0, 0), which is wrong. The usual
    // culprit here is the "connection lost" popup, so we'll temporarily make it
    // visible.
    setConnectionLostPopupVisibleUnlessGoingAway(true);
    dumpComponentRecursively(rootComponent, result.componentLayouts);
    setConnectionLostPopupVisibleUnlessGoingAway(false);

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

export function changeUrl(url: string, replace: boolean): void {
    // Scroll to the top. This has to happen before we change the URL, because
    // if the URL has a #fragment then we will scroll to the corresponding
    // ScrollTarget
    let element = globalThis.RIO_DEBUG_MODE
        ? document.querySelector(".rio-user-root-container-outer")!
        : document.documentElement;

    element.scrollTo({ top: 0, behavior: "smooth" });

    // Change the URL
    if (replace) {
        window.history.replaceState(null, "", url);
    } else {
        window.history.pushState(null, "", url);
    }

    scrollToUrlFragment();
}
