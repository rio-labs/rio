import { DevToolsConnectorComponent } from "./components/devToolsConnector";
import {
    callRemoteMethodDiscardResponse,
    incomingMessageQueue,
    initWebsocket,
} from "./rpc";
import { getPixelsPerRem, scrollToUrlFragment } from "./utils";

// If the devtools are present they are exposed here so the codebase can notify
// them as needed. This is an instance of `DevToolsConnectorComponent`.
export let devToolsConnector: DevToolsConnectorComponent | null = null;

export function setDevToolsConnector(
    connector: DevToolsConnectorComponent
): void {
    devToolsConnector = connector;
}

// Set to indicate that we're intentionally leaving the page. This can be used
// to suppress the connection lost popup, reconnects, or similar
export let goingAway: boolean = false;

export let pixelsPerRem = getPixelsPerRem();
globalThis.pixelsPerRem = pixelsPerRem;

async function main(): Promise<void> {
    // Browsers have a "duplicate tab" feature which can create 2 tabs that
    // share the same session token. We could just try to connect and the server
    // would tell us that the session token is in use, but the server is careful
    // about rejecting connections and thus might make us wait a while. In order
    // to provide a snappier user experience, we'll try to detect a duplicated
    // tab and just reload the page.
    if (isDuplicatedTab()) {
        console.log("Tab appears to have been duplicated; reloading the page");
        window.location.reload();
        return;
    }

    // Display a warning if running in debug mode
    if (globalThis.RIO_DEBUG_MODE) {
        console.warn(
            "Rio is running in DEBUG mode.\nDebug mode includes helpful tools" +
                " for development, but is slower and disables some safety checks." +
                " Never use it in production!"
        );
    }

    window.addEventListener("beforeunload", () => {
        goingAway = true;
    });

    // Note: I'm not sure if this event is ever triggered. The smooth scrolling
    // is actually implemented in `popstate` and in the CSS.
    window.addEventListener("hashchange", (event) => {
        console.log(
            `hashchange event triggered; new URL is ${window.location.href}`
        );

        scrollToUrlFragment();
    });

    // Listen for URL changes, so the session can switch page
    window.addEventListener("popstate", (event: PopStateEvent) => {
        console.debug(
            `popstate event triggered; new URL is ${window.location.href}`
        );

        // This event is also triggered if the user manually types in a URL
        // fragment. So we need to check which part of the url has changed and
        // act accordingly. If it was only the url fragment, we'll simply scroll
        // the relevant ScrollTarget into view.
        //
        // NOTE: If we send a `onUrlChange` message to the server, it'll cause a
        // rebuild of all PageViews and scroll to the top of the page. This is
        // why we *EITHER* send a `onUrlChange` message *OR* scroll to the
        // ScrollTarget, but not both.

        // FIXME: Find a way to tell whether only the url fragment changed
        console.debug(`URL changed to ${window.location.href}`);
        callRemoteMethodDiscardResponse("onUrlChange", {
            new_url: window.location.href.toString(),
        });
    });

    // Process initial messages
    for (let message of globalThis.initialMessages) {
        incomingMessageQueue.push(message);
    }
    delete globalThis.initialMessages;

    // Connect to the websocket
    initWebsocket();
}

function isDuplicatedTab(): boolean {
    // Duplicated tabs share the same `sessionStorage`. So we'll dump our
    // session token into `sessionStorage`, unless it's already there.
    if (sessionStorage.getItem(globalThis.SESSION_TOKEN)) {
        return true;
    }

    sessionStorage.setItem(globalThis.SESSION_TOKEN, "in use");
    return false;
}

main();
