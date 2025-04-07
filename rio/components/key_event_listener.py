from __future__ import annotations

import dataclasses
import typing as t

import imy.docstrings
from uniserde import Jsonable

import rio

from .keyboard_focusable_components import KeyboardFocusableFundamentalComponent

__all__ = [
    "KeyEventListener",
    "HardwareKey",
    "SoftwareKey",
    "NamedSoftwareKey",
    "KeyDownEvent",
    "KeyUpEvent",
    "KeyPressEvent",
]


HardwareKey = t.Literal[
    "unknown",
    # Function keys
    "f1",
    "f2",
    "f3",
    "f4",
    "f5",
    "f6",
    "f7",
    "f8",
    "f9",
    "f10",
    "f11",
    "f12",
    "f13",
    "f14",
    "f15",
    "f16",
    "f17",
    "f18",
    "f19",
    "f20",
    "f21",
    "f22",
    "f23",
    "f24",
    # Digits
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    # Letters
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
    # Punctuation
    "comma",
    "period",
    "semicolon",
    "single-quote",
    "backquote",
    "space",
    # Brackets
    "bracket-left",
    "bracket-right",
    # Math
    "plus",
    "minus",
    "asterisk",
    "slash",
    "equal",
    # Numpad
    "numpad-0",
    "numpad-1",
    "numpad-2",
    "numpad-3",
    "numpad-4",
    "numpad-5",
    "numpad-6",
    "numpad-7",
    "numpad-8",
    "numpad-9",
    "numpad-decimal",
    "numpad-plus",
    "numpad-minus",
    "numpad-asterisk",
    "numpad-slash",
    "numpad-enter",
    "numpad-equal",
    "numpad-comma",
    # Arrow keys
    "arrow-up",
    "arrow-down",
    "arrow-left",
    "arrow-right",
    # Modifiers
    "left-alt",
    "right-alt",
    "left-control",
    "right-control",
    "left-meta",
    "right-meta",
    "left-meta",
    "right-meta",
    "left-shift",
    "right-shift",
    # Toggles
    "caps-lock",
    "num-lock",
    "scroll-lock",
    "fn-lock",
    # Browser
    "browser-back",
    "browser-favorites",
    "browser-forward",
    "browser-home",
    "browser-refresh",
    "browser-search",
    "browser-stop",
    # Media
    "media-play-pause",
    "media-track-next",
    "media-track-previous",
    "media-stop",
    "media-select",
    "media-eject",
    "media-eject",  # Alias of MediaEject
    "volume-down",
    "volume-up",
    "volume-down",  # Alias of VolumeDown
    "volume-up",  # Alias of VolumeUp
    "volume-mute",
    # Apps
    "launch-app-1",
    "launch-app-2",
    "launch-mail",
    # Power
    "power",
    "sleep",
    "wake-up",
    # Clipboard
    "copy",
    "cut",
    "paste",
    # Languages
    "lang-1",
    "lang-2",
    "lang-3",
    "lang-4",
    # Misc
    "escape",
    "tab",
    "enter",
    "delete",
    "insert",
    "home",
    "end",
    "page-up",
    "page-down",
    "pause",
    "print-screen",
    "context-menu",
    "help",
    "backspace",
    "convert",
    "non-convert",
    "backslash",
    "left-backslash",
    "undo",
    "kana-mode",
    "intl-ro",
    "intl-yen",
    "fn",
    "again",
    "props",
    "select",
    "execute",
    "find",
    "cancel",
    "redo",
    "zoom-in",
    "zoom-out",
    "clear",
    "brightness-up",
    "brightness-down",
]

NamedSoftwareKey = t.Literal[
    "unknown",
    # Modifiers
    "alt",
    "control",
    "meta",
    "meta",
    "shift",
    "alt-graph",
    "caps-lock",
    "num-lock",
    "scroll-lock",
    "fn",
    "fn-lock",
    "super",
    "hyper",
    "symbol",
    "symbol-lock",
    # Whitespace
    "enter",
    "tab",
    "space",
    # Navigation
    "arrow-down",
    "arrow-left",
    "arrow-right",
    "arrow-up",
    "end",
    "home",
    "page-down",
    "page-up",
    # Editing
    "backspace",
    "clear",
    "copy",
    "cursor-select",
    "cut",
    "delete",
    "erase-eof",
    "extend-selection",
    "insert",
    "paste",
    "redo",
    "undo",
    # UI
    "accept",
    "again",
    "attention",
    "cancel",
    "context-menu",
    "escape",
    "execute",
    "find",
    "finish",
    "help",
    "pause",
    "play",
    "props",
    "select",
    "zoom-in",
    "zoom-out",
    # Device
    "brightness-down",
    "brightness-up",
    "eject",
    "log-off",
    "power",
    "power-off",
    "print-screen",
    "hibernate",
    "standby",
    "wake-up",
    # IME and composition
    "all-candidates",
    "alphanumeric",
    "code-input",
    "compose",
    "convert",
    "dead",
    "final-mode",
    "group-first",
    "group-last",
    "group-next",
    "group-previous",
    "mode-change",
    "next-candidate",
    "non-convert",
    "previous-candidate",
    "process",
    "single-candidate",
    # Korean
    "hangul-mode",
    "hanja-mode",
    "junja-mode",
    # Japanese
    "eisu",
    "hankaku",
    "hiragana",
    "hiragana-katakana",
    "kana-mode",
    "kanji-mode",
    "katakana",
    "romaji",
    "zenkaku",
    "zenkaku-hanaku",
    # Function
    "f1",
    "f2",
    "f3",
    "f4",
    "f5",
    "f6",
    "f7",
    "f8",
    "f9",
    "f10",
    "f11",
    "f12",
    "f13",
    "f14",
    "f15",
    "f16",
    "f17",
    "f18",
    "f19",
    "f20",
    "f21",  # TODO: According to MDN they only go up to F20
    "f22",
    "f23",
    "f24",
    "soft-1",
    "soft-2",
    "soft-3",
    "soft-4",
    # Phone
    "app-switch",
    "call",
    "camera",
    "camera-focus",
    "end-call",
    "go-back",
    "go-home",
    "headset-hook",
    "last-number-redial",
    "notification",
    "manner-mode",
    "voice-dial",
    # Multimedia
    "channel-down",
    "channel-up",
    "media-fast-forward",
    "media-pause",
    "media-play",
    "media-play-pause",
    "media-record",
    "media-rewind",
    "media-stop",
    "media-track-next",
    "media-track-previous",
    # Audio control
    # TODO: I stopped checking MDN at this point, this is purely Copilot now
    "audio-balance-left",
    "audio-balance-right",
    "audio-bass-down",
    "audio-bass-boost-down",
    "audio-bass-boost-toggle",
    "audio-bass-boost-up",
    "audio-bass-up",
    "audio-fader-front",
    "audio-fader-rear",
    "audio-surround-mode-next",
    "audio-treble-down",
    "audio-treble-up",
    "audio-volume-down",
    "audio-volume-mute",
    "audio-volume-up",
    "microphone-toggle",
    "microphone-volume-down",
    "microphone-volume-mute",
    "microphone-volume-up",
    # TV control
    "tv",
    "tv-3d-mode",
    "tv-antenna-cable",
    "tv-audio-description",
    "tv-audio-description-mix-down",
    "tv-audio-description-mix-up",
    "tv-contents-menu",
    "tv-data-service",
    "tv-input",
    "tv-input-component-1",
    "tv-input-component-2",
    "tv-input-composite-1",
    "tv-input-composite-2",
    "tv-input-hdmi-1",
    "tv-input-hdmi-2",
    "tv-input-hdmi-3",
    "tv-input-hdmi-4",
    "tv-input-vga-1",
    "tv-media-context",
    "tv-network",
    "tv-number-entry",
    "tv-power",
    "tv-radio-service",
    "tv-satellite",
    "tv-satellite-bs",
    "tv-satellite-cs",
    "tv-satellite-toggle",
    "tv-terrestrial-analog",
    "tv-terrestrial-digital",
    "tv-timer",
    # Media controller
    "avr-input",
    "avr-power",
    "color-f0-red",
    "color-f1-green",
    "color-f2-yellow",
    "color-f3-blue",
    "color-f4-gray",
    "color-f5-brown",
    "closed-caption-toggle",
    "dimmer",
    "display-swap",
    "dvr",
    "exit",
    "favorite-clear-0",
    "favorite-clear-1",
    "favorite-clear-2",
    "favorite-clear-3",
    "favorite-recall-0",
    "favorite-recall-1",
    "favorite-recall-2",
    "favorite-recall-3",
    "favorite-store-0",
    "favorite-store-1",
    "favorite-store-2",
    "favorite-store-3",
    "guide",
    "guide-next-day",
    "guide-previous-day",
    "info",
    "instant-replay",
    "link",
    "list-program",
    "live-content",
    "lock",
    "media-apps",
    "media-audio-track",
    "media-last",
    "media-skip-backward",
    "media-skip-forward",
    "media-step-backward",
    "media-step-forward",
    "media-top-menu",
    "navigate-in",
    "navigate-next",
    "navigate-out",
    "navigate-previous",
    "next-favorite-channel",
    "next-user-profile",
    "on-demand",
    "pairing",
    "pin-p-down",
    "pin-p-move",
    "pin-p-toggle",
    "pin-p-up",
    "play-speed-down",
    "play-speed-reset",
    "play-speed-up",
    "random-toggle",
    "rc-low-battery",
    "record-speed-next",
    "rf-bypass",
    "scan-channels-toggle",
    "screen-mode-next",
    "settings",
    "split-screen-toggle",
    "stb-input",
    "stb-power",
    "subtitle",
    "teletext",
    "video-mode-next",
    "wink",
    "zoom-toggle",
    # Speech recognition
    "speech-correction-list",
    "speech-input-toggle",
    # Document
    "close",
    "new",
    "open",
    "print",
    "save",
    "spell-check",
    "mail-forward",
    "mail-reply",
    "mail-send",
    # Application launcher
    "launch-calculator",
    "launch-calendar",
    "launch-contacts",
    "launch-mail",
    "launch-media-player",
    "launch-music-player",
    "launch-my-computer",
    "launch-phone",
    "launch-screen-saver",
    "launch-spreadsheet",
    "launch-web-browser",
    "launch-web-cam",
    "launch-word-processor",
    "launch-application-1",
    "launch-application-2",
    "launch-application-3",
    "launch-application-4",
    "launch-application-5",
    "launch-application-6",
    "launch-application-7",
    "launch-application-8",
    "launch-application-9",
    "launch-application-10",
    "launch-application-11",
    "launch-application-12",
    "launch-application-13",
    "launch-application-14",
    "launch-application-15",
    "launch-application-16",
    # Browser
    "browser-back",
    "browser-favorites",
    "browser-forward",
    "browser-home",
    "browser-refresh",
    "browser-search",
    "browser-stop",
    # Numeric keypad
    "decimal",
    "key-11",
    "key-12",
    "asterisk",
    "plus",
    "slash",
    "minus",
    "separator",
]
SoftwareKey = NamedSoftwareKey | str

ModifierKey = t.Literal["alt", "control", "meta", "shift"]
KeyCombination = (
    SoftwareKey
    | tuple[ModifierKey, SoftwareKey]
    | tuple[ModifierKey, ModifierKey, SoftwareKey]
    | tuple[ModifierKey, ModifierKey, ModifierKey, SoftwareKey]
    | tuple[ModifierKey, ModifierKey, ModifierKey, ModifierKey, SoftwareKey]
)

_MODIFIERS: tuple[ModifierKey, ...] = t.get_args(ModifierKey)
NAMED_SOFTWARE_KEYS = frozenset(t.get_args(NamedSoftwareKey))


@dataclasses.dataclass(frozen=True)
class _KeyUpDownEvent:
    """
    Holds information about a key event.

    This is a simple dataclass that stores useful information about a key event.
    You'll typically receive this as argument in events related to key presses.

    ## Attributes

    `hardware_key`: The name of the physical button on the keyboard.

    `software_key`: The name of the button. Depending on the user's keyboard
        layout, this may differ from the `hardware_key`. (For example, if the
        physical keyboard has a QWERTY layout but the OS is configured to use
        Dvorak.)

    `text`: The text that pressing this button produces. For example, Shift+1
        produces the text "!". If the button doesn't produce any text, like F1
        for example, this will be an empty string.

    `modifiers`: The names of the modifier keys (control, shift, alt, meta) that
        were pressed when the event occurred.
    """

    hardware_key: HardwareKey
    software_key: SoftwareKey
    text: str
    modifiers: frozenset[ModifierKey]

    @classmethod
    def _from_json(cls, json_data: dict[str, t.Any]):
        result = cls(
            hardware_key=json_data["hardwareKey"],
            software_key=json_data["softwareKey"],
            text=json_data["text"],
            modifiers=frozenset(json_data["modifiers"]),
        )

        assert isinstance(result.hardware_key, str)
        assert isinstance(result.software_key, str)
        assert isinstance(result.text, str)
        assert all(isinstance(modifier, str) for modifier in result.modifiers)

        return result

    def __str__(self) -> str:
        keys = [
            key
            for key in _MODIFIERS
            if key in self.modifiers and key != self.software_key
        ]
        keys.append(self.software_key)

        return " + ".join(keys)


@t.final
@imy.docstrings.mark_constructor_as_private
class KeyDownEvent(_KeyUpDownEvent):
    pass


@t.final
@imy.docstrings.mark_constructor_as_private
class KeyUpEvent(_KeyUpDownEvent):
    pass


@t.final
@imy.docstrings.mark_constructor_as_private
class KeyPressEvent(_KeyUpDownEvent):
    pass


E = t.TypeVar("E", KeyDownEvent, KeyUpEvent, KeyPressEvent)


@t.final
class KeyEventListener(KeyboardFocusableFundamentalComponent):
    """
    Calls an event handler when a key is pressed or released.

    `KeyEventListener` is a container for a single child component. It reports
    any key-related user interactions that occur within that child component.

    Keep in mind that `KeyEventListener` will only report events that have not
    already been handled by a child component. For example, typing into a
    `TextInput` will not trigger a parent `KeyEventListener`, since the
    `TextInput` already handles key presses itself.


    ## Attributes

    `content`: The child component.

    `on_key_down`: A function to call when a key is pressed down.

    `on_key_up`: A function to call when a key is released.

    `on_key_press`: A function to call repeatedly while a key is held down.
    """

    content: rio.Component
    _: dataclasses.KW_ONLY
    on_key_down: (
        rio.EventHandler[KeyDownEvent]
        | t.Mapping[KeyCombination, rio.EventHandler[KeyDownEvent]]
    ) = None
    on_key_up: (
        rio.EventHandler[KeyUpEvent]
        | t.Mapping[KeyCombination, rio.EventHandler[KeyUpEvent]]
    ) = None
    on_key_press: (
        rio.EventHandler[KeyPressEvent]
        | t.Mapping[KeyCombination, rio.EventHandler[KeyPressEvent]]
    ) = None

    def __post_init__(self):
        # TODO: These values are never updated, which is a problem if someone
        # uses an attribute binding to change our event handlers
        self._on_key_down = keycombos_to_frozensets(self.on_key_down)
        self._on_key_up = keycombos_to_frozensets(self.on_key_up)
        self._on_key_press = keycombos_to_frozensets(self.on_key_press)

    def _custom_serialize_(self) -> dict[str, Jsonable]:
        return {
            "reportKeyDown": serialize_one_handler(self._on_key_down),
            "reportKeyUp": serialize_one_handler(self._on_key_up),
            "reportKeyPress": serialize_one_handler(self._on_key_press),
        }

    async def _on_message_(self, msg: t.Any) -> None:
        # Parse the message
        assert isinstance(msg, dict), msg

        msg_type: str = msg["type"]
        assert isinstance(msg_type, str), msg_type

        # Dispatch the correct event
        if msg_type == "KeyDown":
            await self._call_key_event_handler(
                self._on_key_down,
                KeyDownEvent._from_json(msg),
            )

        elif msg_type == "KeyUp":
            await self._call_key_event_handler(
                self._on_key_up,
                KeyUpEvent._from_json(msg),
            )

        elif msg_type == "KeyPress":
            await self._call_key_event_handler(
                self._on_key_press,
                KeyPressEvent._from_json(msg),
            )

        else:
            raise ValueError(
                f"{__class__.__name__} encountered unknown message: {msg}"
            )

    async def _call_key_event_handler(
        self,
        handler: rio.EventHandler[E]
        | t.Mapping[frozenset[SoftwareKey], rio.EventHandler[E]],
        event: E,
    ) -> None:
        if handler is None:
            return

        if callable(handler):
            await self.call_event_handler(handler, event)
            return

        # If we have a mapping of event handlers, look up the one that
        # corresponds to this key combination
        key_combination = set[SoftwareKey]()
        key_combination.update(event.modifiers)
        key_combination.add(event.software_key)

        try:
            handler = handler[frozenset(key_combination)]
        except KeyError:
            return

        await self.call_event_handler(handler, event)


KeyEventListener._unique_id_ = "KeyEventListener-builtin"


def keycombos_to_frozensets(
    handler: rio.EventHandler | t.Mapping[KeyCombination, rio.EventHandler],
) -> rio.EventHandler | t.Mapping[frozenset[SoftwareKey], rio.EventHandler]:
    """
    Users provide key combinations as tuples, but since order of the keys
    doesn't matter, we convert them to frozensets.

    While we're at it, we'll also validate the inputs.
    """
    if handler is None:
        return handler

    if callable(handler):
        return handler

    result = dict[frozenset[SoftwareKey], rio.EventHandler]()

    for key_combination, handler in handler.items():
        if isinstance(key_combination, str):
            key_combination = t.cast(list[SoftwareKey], [key_combination])

        frozen_combination = frozenset(key_combination)
        if len(frozen_combination) != len(key_combination):
            raise ValueError(
                f"Duplicate key in key combination: {key_combination}"
            )

        for key in key_combination:
            if key in NAMED_SOFTWARE_KEYS:
                continue

            if len(key) != 1:
                raise ValueError(f"Invalid key in key combination: {key!r}")

            # if not key.islower():
            #     raise ValueError(
            #         f"Invalid key in key combination: {key!r} (Keys must be lower case)"
            #     )

        result[frozen_combination] = handler

    return result


def serialize_one_handler(
    handler: rio.EventHandler
    | t.Mapping[frozenset[SoftwareKey], rio.EventHandler],
) -> Jsonable:
    if not handler:
        return []
    elif callable(handler):
        return True
    else:
        return [list(combination) for combination in handler.keys()]
