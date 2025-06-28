import { goingAway, pixelsPerRem } from "./app";
import { componentsById, updateComponentStates } from "./componentManagement";
import { KeyboardFocusableComponent } from "./components/keyboardFocusableComponent";
import {
    requestFileUpload,
    registerFont,
    closeSession,
    setTitle,
    getUnittestClientLayoutInfo,
    getComponentLayouts,
    removeDialog,
    changeUrl,
} from "./rpcFunctions";
import {
    setClipboard,
    getClipboard,
    ClipboardError,
    getPreferredPythonDateFormatString,
    sleep,
    getScrollBarSizeInPixels,
} from "./utils";
import { AsyncQueue } from "./utils";

let websocket: WebSocket | null = null;
let pingPongHandlerId: number;
export let incomingMessageQueue: AsyncQueue<JsonRpcMessage> = new AsyncQueue();

export type JsonRpcMessage = {
    jsonrpc: "2.0";
    id?: number;
    method?: string;
    params?: any;
};

export type JsonRpcResponse = {
    jsonrpc: "2.0";
    id: number;
    result?: any;
    error?: {
        code: number;
        message: string;
    };
};

export function setConnectionLostPopupVisibleUnlessGoingAway(
    visible: boolean
): void {
    // If the user is intentionally leaving, don't annoy them with a popup
    if (goingAway) {
        return;
    }

    // Find the component
    let connectionLostPopupContainer = document.querySelector(
        ".rio-connection-lost-popup-container"
    ) as HTMLElement | null;

    if (connectionLostPopupContainer === null) {
        return;
    }

    // Update it
    if (visible) {
        connectionLostPopupContainer.classList.add(
            "rio-connection-lost-popup-visible"
        );
    } else {
        connectionLostPopupContainer.classList.remove(
            "rio-connection-lost-popup-visible"
        );
    }
}

globalThis.setConnectionLostPopupVisible =
    setConnectionLostPopupVisibleUnlessGoingAway;

// Because processing incoming messages is async, we can't just attach our
// function to `websocket.onMessage`. That could lead to multiple messages being
// processed at the same time, which can cause problems. (For example, when a new
// font is registered, we have to wait until the font is loaded before
// processing any `updateComponentStates` messages. Otherwise the layouting will
// happen with the incorrect font.)
//
// To work around this problem, all incoming messages are simply pushed into a
// queue and then processed in order by this async worker here.
async function processMessages(): Promise<void> {
    while (true) {
        let message = await incomingMessageQueue.get();

        let response = await processMessageReturnResponse(message);

        if (response !== null) {
            sendMessageOverWebsocket(response);
        }
    }
}
processMessages();

function createWebsocket(): void {
    // If the user is leaving the page, don't try to connect anymore. This could
    // prevent the user from leaving.
    if (goingAway) {
        return;
    }

    let url = new URL(
        `${globalThis.RIO_BASE_URL}rio/ws?session_token=${globalThis.SESSION_TOKEN}`,
        window.location.href
    );
    url.protocol = url.protocol.replace("http", "ws");
    console.log(`Connecting websocket to ${url.href}`);
    websocket = new WebSocket(url.href);

    websocket.addEventListener("open", onOpen);
    websocket.addEventListener("message", onMessage);
    websocket.addEventListener("error", onError);
    websocket.addEventListener("close", onClose);
}

export function initWebsocket(): void {
    createWebsocket();
    websocket!.addEventListener("open", sendInitialMessage);
}

/// Send the initial message with device, user & platform information to the
/// server
function sendInitialMessage(): void {
    // User Settings
    let userSettings = {};
    for (let key in localStorage) {
        if (!key.startsWith("rio:userSetting:")) {
            continue;
        }

        try {
            userSettings[key.slice("rio:userSetting:".length)] = JSON.parse(
                localStorage[key]
            );
        } catch (e) {
            console.warn(`Failed to parse user setting ${key}: ${e}`);
        }
    }

    // The names of all months
    const monthFormatter = new Intl.DateTimeFormat("default", {
        month: "long",
    });
    const monthNamesLong: string[] = [];

    for (let month = 0; month < 12; month++) {
        const date = new Date(2000, month, 1);
        monthNamesLong.push(monthFormatter.format(date));
    }

    // The names of all days
    const dayFormatter = new Intl.DateTimeFormat("default", {
        weekday: "long",
    });
    const dayNamesLong: string[] = [];

    for (let day = 0; day < 7; day++) {
        const date = new Date(2000, 0, day + 3);
        dayNamesLong.push(dayFormatter.format(date));
    }

    // Date format string
    let dateFormatString = getPreferredPythonDateFormatString("default");

    // Decimal separator
    let decimalSeparator = (1.1).toLocaleString().replace(/1/g, "");

    // Thousands separator
    let thousandsSeparator = (1111).toLocaleString().replace(/1/g, "");

    let windowRect = document.documentElement.getBoundingClientRect();

    sendMessageOverWebsocket({
        url: document.location.href,
        // User information
        userSettings: userSettings,
        prefersLightTheme: !window.matchMedia("(prefers-color-scheme: dark)")
            .matches,
        // Internationalization
        preferredLanguages: navigator.languages,
        monthNamesLong: monthNamesLong,
        dayNamesLong: dayNamesLong,
        dateFormatString: dateFormatString,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        decimalSeparator: decimalSeparator,
        thousandsSeparator: thousandsSeparator,
        // Platform information
        screenWidth: screen.width / pixelsPerRem,
        screenHeight: screen.height / pixelsPerRem,
        windowWidth: windowRect.width / pixelsPerRem,
        windowHeight: windowRect.height / pixelsPerRem,
        physicalPixelsPerFontHeight: pixelsPerRem * window.devicePixelRatio,
        scrollBarSize: getScrollBarSizeInPixels() / pixelsPerRem,
        primaryPointerType: window.matchMedia("(pointer: coarse)").matches
            ? "touch"
            : "mouse",
    });
}

function onOpen(): void {
    console.log("Websocket connection opened");

    setConnectionLostPopupVisibleUnlessGoingAway(false);

    // Some proxies kill idle websocket connections. Send pings occasionally to
    // keep the connection alive.
    pingPongHandlerId = setInterval(() => {
        sendMessageOverWebsocket({
            jsonrpc: "2.0",
            method: "ping",
            params: ["ping"],
            id: `ping-${Date.now()}`,
        });
    }, globalThis.PING_PONG_INTERVAL_SECONDS * 1000);
}

function onMessage(event: MessageEvent<string>) {
    // Parse the message JSON
    let message = JSON.parse(event.data);

    // Print a copy of the message because some messages are modified in-place
    // when they're processed
    console.debug("Received message: ", JSON.parse(event.data));

    // Push it into the queue, to be processed as soon as the previous message
    // has been processed
    incomingMessageQueue.push(message);
}

function onError(event: Event) {
    console.warn(`Websocket error`);
}

async function onClose(event: CloseEvent) {
    console.log(`Websocket connection closed with code ${event.code}`);

    // Stop sending pings
    clearInterval(pingPongHandlerId);

    // If the user is leaving the page, do nothing. Reconnecting the websocket
    // might even prevent the browser from navigating away and trap the user
    // here.
    if (goingAway) {
        return;
    }

    // Show the user that the connection was lost
    setConnectionLostPopupVisibleUnlessGoingAway(true);

    // Check the status code
    if (event.code === 3000) {
        // Invalid session token
        console.error(
            "Reloading the page because the session token is invalid"
        );
        window.location.reload();
        return;
    }

    startTryingToReconnect();
}

async function startTryingToReconnect() {
    // Some browsers deliberately slow down websocket reconnects, which is why
    // this function polls with HTTP requests instead.

    let maxAttempts = globalThis.RIO_DEBUG_MODE ? Infinity : 10;

    for (
        let connectionAttempt = 1;
        connectionAttempt < maxAttempts;
        connectionAttempt++
    ) {
        // Wait a bit before trying to reconnect (again)
        let delay: number;
        if (globalThis.RIO_DEBUG_MODE) {
            delay = 0.5;
        } else {
            delay = 2 ** connectionAttempt - 1; // 1 3 7 15 31 63 ...
            delay = Math.min(delay, 300); // Never wait longer than 5min
        }

        console.log(`Will attempt to reconnect in ${delay} seconds`);
        await sleep(delay);

        let tokenIsValid: boolean;
        try {
            let response = await fetch(
                `${globalThis.RIO_BASE_URL}rio/validate-token?session_token=${globalThis.SESSION_TOKEN}`
            );
            tokenIsValid = await response.json();
        } catch {
            continue;
        }

        if (tokenIsValid) {
            console.log(
                "Session token is still valid; re-establishing websocket connection"
            );
            createWebsocket();
        } else {
            console.log("Session token is no longer valid; reloading the page");
            document.location.reload();
        }
        return;
    }

    console.warn(`Websocket connection closed. Giving up trying to reconnect.`);
}

export function sendMessageOverWebsocket(message: object) {
    if (!websocket) {
        console.error(
            `Attempted to send message, but the websocket is not connected: ${message}`
        );
        return;
    }

    console.debug("Sending message: ", message);

    websocket.send(JSON.stringify(message));
}

export function callRemoteMethodDiscardResponse(
    method: string,
    params: object
) {
    sendMessageOverWebsocket({
        jsonrpc: "2.0",
        method: method,
        params: params,
    });
}

export async function processMessageReturnResponse(
    message: JsonRpcMessage
): Promise<JsonRpcResponse | null> {
    // If this isn't a method call, ignore it
    if (message.method === undefined) {
        return null;
    }

    // Delegate to the appropriate handler
    let response: any;
    let responseIsError = false;

    switch (message.method) {
        case "updateComponentStates":
            // The component states have changed, and new components may have been
            // introduced.
            updateComponentStates(
                message.params.delta_states,
                message.params.root_component_id
            );
            response = null;
            break;

        case "evaluateJavaScript":
        case "evaluateJavaScriptAndGetResult":
            // Allow the server to run JavaScript
            //
            // Avoid using `eval` so that the code can be minified
            try {
                const func = new Function(message.params.java_script_source);
                response = func();

                if (response === undefined) {
                    response = null;
                }
            } catch (e) {
                response = e.toString();
                responseIsError = true;
                console.warn(
                    `Uncaught exception in \`evaluateJavaScript\`: ${e}`
                );
            }
            break;

        case "changeUrl":
            changeUrl(message.params.url, message.params.replace);
            response = null;
            break;

        case "setKeyboardFocus":
            let component = componentsById[message.params.component_id]!;

            if (component instanceof KeyboardFocusableComponent) {
                component.grabKeyboardFocus();
            }

            response = null;
            break;

        case "setTitle":
            setTitle(message.params.title);
            response = null;
            break;

        case "requestFileUpload":
            // Upload a file to the server
            requestFileUpload(message.params);
            response = null;
            break;

        case "setUserSettings":
            // Persistently store user settings
            for (let key in message.params.delta_settings) {
                localStorage.setItem(
                    `rio:userSetting:${key}`,
                    JSON.stringify(message.params.delta_settings[key])
                );
            }
            response = null;
            break;

        case "registerFont":
            // Load and register a new font
            //
            // Note: No `await` here because that only slows us down. We don't
            // gain anything from waiting for it to finish.
            registerFont(message.params.name, message.params.urls);
            response = null;
            break;

        case "applyTheme":
            // Set the CSS variables
            for (let key in message.params.css_variables) {
                document.documentElement.style.setProperty(
                    key,
                    message.params.css_variables[key]
                );
            }

            // Set the theme variant
            document.documentElement.setAttribute(
                "data-theme",
                message.params.theme_variant
            );

            // Remove the default anti-flashbang color
            document.documentElement.style.background = "";

            response = null;
            break;

        case "closeSession":
            closeSession();
            response = null;
            break;

        case "setClipboard":
            try {
                await setClipboard(message.params.text);
                response = null;
            } catch (e) {
                response = e.toString();
                responseIsError = true;
                if (e instanceof ClipboardError) {
                    console.warn(`ClipboardError: ${e.message}`);
                } else {
                    console.warn(
                        `Uncaught exception in \`setClipboard\`: ${e}`
                    );
                }
            }
            break;

        case "getClipboard":
            try {
                response = await getClipboard();
            } catch (e) {
                response = e.toString();
                responseIsError = true;
                if (e instanceof ClipboardError) {
                    console.warn(`ClipboardError: ${e.message}`);
                } else {
                    console.warn(
                        `Uncaught exception in \`getClipboard\`: ${e}`
                    );
                }
            }
            break;

        case "getComponentLayouts":
            response = getComponentLayouts(message.params.component_ids);
            break;

        case "getUnittestClientLayoutInfo":
            response = await getUnittestClientLayoutInfo();
            break;

        case "removeDialog":
            removeDialog(message.params.root_component_id);
            break;

        default:
            // Invalid method
            throw `Encountered unknown RPC method: ${message.method}`;
    }

    if (message.id === undefined) {
        return null;
    }

    let rpcResponse: JsonRpcResponse = {
        jsonrpc: "2.0",
        id: message.id,
    };

    if (responseIsError) {
        rpcResponse["error"] = {
            code: -32000,
            message: response as string,
        };
    } else {
        rpcResponse["result"] = response;
    }

    return rpcResponse;
}
