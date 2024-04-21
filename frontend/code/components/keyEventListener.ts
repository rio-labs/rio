import { SingleContainer } from './singleContainer';
import { ComponentBase, ComponentState } from './componentBase';
import { ComponentId } from '../dataModels';
import { firstDefined } from '../utils';

// https://developer.mozilla.org/en-US/docs/Web/API/UI_Events/Keyboard_event_code_values
const HARDWARE_KEY_MAP = {
    Unidentified: 'unknown',
    '': 'unknown',

    // Function keys
    F1: 'f1',
    F2: 'f2',
    F3: 'f3',
    F4: 'f4',
    F5: 'f5',
    F6: 'f6',
    F7: 'f7',
    F8: 'f8',
    F9: 'f9',
    F10: 'f10',
    F11: 'f11',
    F12: 'f12',
    F13: 'f13',
    F14: 'f14',
    F15: 'f15',
    F16: 'f16',
    F17: 'f17',
    F18: 'f18',
    F19: 'f19',
    F20: 'f20',
    F21: 'f21',
    F22: 'f22',
    F23: 'f23',
    F24: 'f24',

    // Digits
    Digit0: '0',
    Digit1: '1',
    Digit2: '2',
    Digit3: '3',
    Digit4: '4',
    Digit5: '5',
    Digit6: '6',
    Digit7: '7',
    Digit8: '8',
    Digit9: '9',

    // Letters
    KeyA: 'a',
    KeyB: 'b',
    KeyC: 'c',
    KeyD: 'd',
    KeyE: 'e',
    KeyF: 'f',
    KeyG: 'g',
    KeyH: 'h',
    KeyI: 'i',
    KeyJ: 'j',
    KeyK: 'k',
    KeyL: 'l',
    KeyM: 'm',
    KeyN: 'n',
    KeyO: 'o',
    KeyP: 'p',
    KeyQ: 'q',
    KeyR: 'r',
    KeyS: 's',
    KeyT: 't',
    KeyU: 'u',
    KeyV: 'v',
    KeyW: 'w',
    KeyX: 'x',
    KeyY: 'y',
    KeyZ: 'z',

    // Punctuation
    Comma: 'comma',
    Period: 'period',
    Semicolon: 'semicolon',
    Quote: 'single-quote',
    Backquote: 'backquote',
    Space: 'space',

    // Brackets
    BracketLeft: 'bracket-left',
    BracketRight: 'bracket-right',

    // Math
    Plus: 'plus',
    Minus: 'minus',
    Multiply: 'asterisk',
    Slash: 'slash',
    Equal: 'equal',

    // Numpad
    Numpad0: 'numpad-0',
    Numpad1: 'numpad-1',
    Numpad2: 'numpad-2',
    Numpad3: 'numpad-3',
    Numpad4: 'numpad-4',
    Numpad5: 'numpad-5',
    Numpad6: 'numpad-6',
    Numpad7: 'numpad-7',
    Numpad8: 'numpad-8',
    Numpad9: 'numpad-9',
    NumpadDecimal: 'numpad-decimal',
    NumpadAdd: 'numpad-plus',
    NumpadSubtract: 'numpad-minus',
    NumpadMultiply: 'numpad-asterisk',
    NumpadDivide: 'numpad-slash',
    NumpadEnter: 'numpad-enter',
    NumpadEqual: 'numpad-equal',
    NumpadComma: 'numpad-comma',

    // Arrow keys
    ArrowUp: 'arrow-up',
    ArrowDown: 'arrow-down',
    ArrowLeft: 'arrow-left',
    ArrowRight: 'arrow-right',

    // Modifiers
    AltLeft: 'left-alt',
    AltRight: 'right-alt',
    ControlLeft: 'left-control',
    ControlRight: 'right-control',
    MetaLeft: 'left-meta',
    MetaRight: 'right-meta',
    OSLeft: 'left-meta',
    OSRight: 'right-meta',
    ShiftLeft: 'left-shift',
    ShiftRight: 'right-shift',

    // Toggles
    CapsLock: 'caps-lock',
    NumLock: 'num-lock',
    ScrollLock: 'scroll-lock',
    FnLock: 'fn-lock',

    // Browser
    BrowserBack: 'browser-back',
    BrowserFavorites: 'browser-favorites',
    BrowserForward: 'browser-forward',
    BrowserHome: 'browser-home',
    BrowserRefresh: 'browser-refresh',
    BrowserSearch: 'browser-search',
    BrowserStop: 'browser-stop',

    // Media
    MediaPlayPause: 'media-play-pause',
    MediaTrackNext: 'media-track-next',
    MediaTrackPrevious: 'media-track-previous',
    MediaStop: 'media-stop',
    MediaSelect: 'media-select',
    MediaEject: 'media-eject',
    Eject: 'media-eject', // Alias of MediaEject
    VolumeDown: 'volume-down',
    VolumeUp: 'volume-up',
    AudioVolumeDown: 'volume-down', // Alias of VolumeDown
    AudioVolumeUp: 'volume-up', // Alias of VolumeUp
    AudioVolumeMute: 'volume-mute',

    // Apps
    LaunchApp1: 'launch-app-1',
    LaunchApp2: 'launch-app-2',
    LaunchMail: 'launch-mail',

    // Power
    Power: 'power',
    Sleep: 'sleep',
    WakeUp: 'wake-up',

    // Clipboard
    Copy: 'copy',
    Cut: 'cut',
    Paste: 'paste',

    // Languages
    Lang1: 'lang-1',
    Lang2: 'lang-2',
    Lang3: 'lang-3',
    Lang4: 'lang-4',

    // Misc
    Escape: 'escape',
    Tab: 'tab',
    Enter: 'enter',
    Delete: 'delete',
    Insert: 'insert',
    Home: 'home',
    End: 'end',
    PageUp: 'page-up',
    PageDown: 'page-down',
    Pause: 'pause',
    PrintScreen: 'print-screen',
    ContextMenu: 'context-menu',
    Help: 'help',
    Backspace: 'backspace',
    Convert: 'convert',
    NonConvert: 'non-convert',
    Backslash: 'backslash',
    IntlBackslash: 'left-backslash',
    Undo: 'undo',
    KanaMode: 'kana-mode',
    IntlRo: 'intl-ro',
    IntlYen: 'intl-yen',
    Fn: 'fn',
    Again: 'again',
    Props: 'props',
    Select: 'select',
    Execute: 'execute',
    Find: 'find',
    Cancel: 'cancel',
    Redo: 'redo',
    ZoomIn: 'zoom-in',
    ZoomOut: 'zoom-out',
    Clear: 'clear',
    BrightnessUp: 'brightness-up',
    BrightnessDown: 'brightness-down',
} as const;

// https://developer.mozilla.org/en-US/docs/Web/API/UI_Events/Keyboard_event_key_values
const SOFTWARE_KEY_MAP = {
    Unidentified: 'unknown',
    '': 'unknown',

    // Modifiers
    Alt: 'alt',
    Control: 'control',
    Meta: 'meta',
    OS: 'meta',
    Shift: 'shift',
    AltGraph: 'alt-graph',
    CapsLock: 'caps-lock',
    NumLock: 'num-lock',
    ScrollLock: 'scroll-lock',
    Fn: 'fn',
    FnLock: 'fn-lock',
    Super: 'super',
    Hyper: 'hyper',
    Symbol: 'symbol',
    SymbolLock: 'symbol-lock',

    // Whitespace
    Enter: 'enter',
    Tab: 'tab',
    ' ': 'space',

    // Navigation
    ArrowDown: 'arrow-down',
    ArrowLeft: 'arrow-left',
    ArrowRight: 'arrow-right',
    ArrowUp: 'arrow-up',
    End: 'end',
    Home: 'home',
    PageDown: 'page-down',
    PageUp: 'page-up',

    // Editing
    Backspace: 'backspace',
    Clear: 'clear',
    Copy: 'copy',
    CrSel: 'cursor-select',
    Cut: 'cut',
    Delete: 'delete',
    EraseEof: 'erase-eof',
    ExSel: 'extend-selection',
    Insert: 'insert',
    Paste: 'paste',
    Redo: 'redo',
    Undo: 'undo',

    // UI
    Accept: 'accept',
    Again: 'again',
    Attn: 'attention',
    Cancel: 'cancel',
    ContextMenu: 'context-menu',
    Escape: 'escape',
    Execute: 'execute',
    Find: 'find',
    Finish: 'finish',
    Help: 'help',
    Pause: 'pause',
    Play: 'play',
    Props: 'props',
    Select: 'select',
    ZoomIn: 'zoom-in',
    ZoomOut: 'zoom-out',

    // Device
    BrightnessDown: 'brightness-down',
    BrightnessUp: 'brightness-up',
    Eject: 'eject',
    LogOff: 'log-off',
    Power: 'power',
    PowerOff: 'power-off',
    PrintScreen: 'print-screen',
    Hibernate: 'hibernate',
    Standby: 'standby',
    WakeUp: 'wake-up',

    // IME and composition
    AllCandidates: 'all-candidates',
    Alphanumeric: 'alphanumeric',
    CodeInput: 'code-input',
    Compose: 'compose',
    Convert: 'convert',
    Dead: 'dead',
    FinalMode: 'final-mode',
    GroupFirst: 'group-first',
    GroupLast: 'group-last',
    GroupNext: 'group-next',
    GroupPrevious: 'group-previous',
    ModeChange: 'mode-change',
    NextCandidate: 'next-candidate',
    NonConvert: 'non-convert',
    PreviousCandidate: 'previous-candidate',
    Process: 'process',
    SingleCandidate: 'single-candidate',

    // Korean
    HangulMode: 'hangul-mode',
    HanjaMode: 'hanja-mode',
    JunjaMode: 'junja-mode',

    // Japanese
    Eisu: 'eisu',
    Hankaku: 'hankaku',
    Hiragana: 'hiragana',
    HiraganaKatakana: 'hiragana-katakana',
    KanaMode: 'kana-mode',
    KanjiMode: 'kanji-mode',
    Katakana: 'katakana',
    Romaji: 'romaji',
    Zenkaku: 'zenkaku',
    ZenkakuHanaku: 'zenkaku-hanaku',

    // Function
    F1: 'f1',
    F2: 'f2',
    F3: 'f3',
    F4: 'f4',
    F5: 'f5',
    F6: 'f6',
    F7: 'f7',
    F8: 'f8',
    F9: 'f9',
    F10: 'f10',
    F11: 'f11',
    F12: 'f12',
    F13: 'f13',
    F14: 'f14',
    F15: 'f15',
    F16: 'f16',
    F17: 'f17',
    F18: 'f18',
    F19: 'f19',
    F20: 'f20',
    F21: 'f21', // TODO: According to MDN they only go up to F20
    F22: 'f22',
    F23: 'f23',
    F24: 'f24',

    Soft1: 'soft-1',
    Soft2: 'soft-2',
    Soft3: 'soft-3',
    Soft4: 'soft-4',

    // Phone
    AppSwitch: 'app-switch',
    Call: 'call',
    Camera: 'camera',
    CameraFocus: 'camera-focus',
    EndCall: 'end-call',
    GoBack: 'go-back',
    GoHome: 'go-home',
    HeadsetHook: 'headset-hook',
    LastNumberRedial: 'last-number-redial',
    Notification: 'notification',
    MannerMode: 'manner-mode',
    VoiceDial: 'voice-dial',

    // Multimedia
    ChannelDown: 'channel-down',
    ChannelUp: 'channel-up',
    MediaFastForward: 'media-fast-forward',
    MediaPause: 'media-pause',
    MediaPlay: 'media-play',
    MediaPlayPause: 'media-play-pause',
    MediaRecord: 'media-record',
    MediaRewind: 'media-rewind',
    MediaStop: 'media-stop',
    MediaTrackNext: 'media-track-next',
    MediaTrackPrevious: 'media-track-previous',

    // Audio control
    // TODO: I stopped checking MDN at this point, this is purely Copilot now
    AudioBalanceLeft: 'audio-balance-left',
    AudioBalanceRight: 'audio-balance-right',
    AudioBassDown: 'audio-bass-down',
    AudioBassBoostDown: 'audio-bass-boost-down',
    AudioBassBoostToggle: 'audio-bass-boost-toggle',
    AudioBassBoostUp: 'audio-bass-boost-up',
    AudioBassUp: 'audio-bass-up',
    AudioFaderFront: 'audio-fader-front',
    AudioFaderRear: 'audio-fader-rear',
    AudioSurroundModeNext: 'audio-surround-mode-next',
    AudioTrebleDown: 'audio-treble-down',
    AudioTrebleUp: 'audio-treble-up',
    AudioVolumeDown: 'audio-volume-down',
    AudioVolumeMute: 'audio-volume-mute',
    AudioVolumeUp: 'audio-volume-up',
    MicrophoneToggle: 'microphone-toggle',
    MicrophoneVolumeDown: 'microphone-volume-down',
    MicrophoneVolumeMute: 'microphone-volume-mute',
    MicrophoneVolumeUp: 'microphone-volume-up',

    // TV control
    TV: 'tv',
    TV3DMode: 'tv-3d-mode',
    TVAntennaCable: 'tv-antenna-cable',
    TVAudioDescription: 'tv-audio-description',
    TVAudioDescriptionMixDown: 'tv-audio-description-mix-down',
    TVAudioDescriptionMixUp: 'tv-audio-description-mix-up',
    TVContentsMenu: 'tv-contents-menu',
    TVDataService: 'tv-data-service',
    TVInput: 'tv-input',
    TVInputComponent1: 'tv-input-component-1',
    TVInputComponent2: 'tv-input-component-2',
    TVInputComposite1: 'tv-input-composite-1',
    TVInputComposite2: 'tv-input-composite-2',
    TVInputHDMI1: 'tv-input-hdmi-1',
    TVInputHDMI2: 'tv-input-hdmi-2',
    TVInputHDMI3: 'tv-input-hdmi-3',
    TVInputHDMI4: 'tv-input-hdmi-4',
    TVInputVGA1: 'tv-input-vga-1',
    TVMediaContext: 'tv-media-context',
    TVNetwork: 'tv-network',
    TVNumberEntry: 'tv-number-entry',
    TVPower: 'tv-power',
    TVRadioService: 'tv-radio-service',
    TVSatellite: 'tv-satellite',
    TVSatelliteBS: 'tv-satellite-bs',
    TVSatelliteCS: 'tv-satellite-cs',
    TVSatelliteToggle: 'tv-satellite-toggle',
    TVTerrestrialAnalog: 'tv-terrestrial-analog',
    TVTerrestrialDigital: 'tv-terrestrial-digital',
    TVTimer: 'tv-timer',

    // Media controller
    AVRInput: 'avr-input',
    AVRPower: 'avr-power',
    ColorF0Red: 'color-f0-red',
    ColorF1Green: 'color-f1-green',
    ColorF2Yellow: 'color-f2-yellow',
    ColorF3Blue: 'color-f3-blue',
    ColorF4Grey: 'color-f4-grey',
    ColorF5Brown: 'color-f5-brown',
    ClosedCaptionToggle: 'closed-caption-toggle',
    Dimmer: 'dimmer',
    DisplaySwap: 'display-swap',
    DVR: 'dvr',
    Exit: 'exit',
    FavoriteClear0: 'favorite-clear-0',
    FavoriteClear1: 'favorite-clear-1',
    FavoriteClear2: 'favorite-clear-2',
    FavoriteClear3: 'favorite-clear-3',
    FavoriteRecall0: 'favorite-recall-0',
    FavoriteRecall1: 'favorite-recall-1',
    FavoriteRecall2: 'favorite-recall-2',
    FavoriteRecall3: 'favorite-recall-3',
    FavoriteStore0: 'favorite-store-0',
    FavoriteStore1: 'favorite-store-1',
    FavoriteStore2: 'favorite-store-2',
    FavoriteStore3: 'favorite-store-3',
    Guide: 'guide',
    GuideNextDay: 'guide-next-day',
    GuidePreviousDay: 'guide-previous-day',
    Info: 'info',
    InstantReplay: 'instant-replay',
    Link: 'link',
    ListProgram: 'list-program',
    LiveContent: 'live-content',
    Lock: 'lock',
    MediaApps: 'media-apps',
    MediaAudioTrack: 'media-audio-track',
    MediaLast: 'media-last',
    MediaSkipBackward: 'media-skip-backward',
    MediaSkipForward: 'media-skip-forward',
    MediaStepBackward: 'media-step-backward',
    MediaStepForward: 'media-step-forward',
    MediaTopMenu: 'media-top-menu',
    NavigateIn: 'navigate-in',
    NavigateNext: 'navigate-next',
    NavigateOut: 'navigate-out',
    NavigatePrevious: 'navigate-previous',
    NextFavoriteChannel: 'next-favorite-channel',
    NextUserProfile: 'next-user-profile',
    OnDemand: 'on-demand',
    Pairing: 'pairing',
    PinPDown: 'pin-p-down',
    PinPMove: 'pin-p-move',
    PinPToggle: 'pin-p-toggle',
    PinPUp: 'pin-p-up',
    PlaySpeedDown: 'play-speed-down',
    PlaySpeedReset: 'play-speed-reset',
    PlaySpeedUp: 'play-speed-up',
    RandomToggle: 'random-toggle',
    RcLowBattery: 'rc-low-battery',
    RecordSpeedNext: 'record-speed-next',
    RfBypass: 'rf-bypass',
    ScanChannelsToggle: 'scan-channels-toggle',
    ScreenModeNext: 'screen-mode-next',
    Settings: 'settings',
    SplitScreenToggle: 'split-screen-toggle',
    STBInput: 'stb-input',
    STBPower: 'stb-power',
    Subtitle: 'subtitle',
    Teletext: 'teletext',
    VideoModeNext: 'video-mode-next',
    Wink: 'wink',
    ZoomToggle: 'zoom-toggle',

    // Speech recognition
    SpeechCorrectionList: 'speech-correction-list',
    SpeechInputToggle: 'speech-input-toggle',

    // Document
    Close: 'close',
    New: 'new',
    Open: 'open',
    Print: 'print',
    Save: 'save',
    SpellCheck: 'spell-check',
    MailForward: 'mail-forward',
    MailReply: 'mail-reply',
    MailSend: 'mail-send',

    // Application launcher
    LaunchCalculator: 'launch-calculator',
    LaunchCalendar: 'launch-calendar',
    LaunchContacts: 'launch-contacts',
    LaunchMail: 'launch-mail',
    LaunchMediaPlayer: 'launch-media-player',
    LaunchMusicPlayer: 'launch-music-player',
    LaunchMyComputer: 'launch-my-computer',
    LaunchPhone: 'launch-phone',
    LaunchScreenSaver: 'launch-screen-saver',
    LaunchSpreadsheet: 'launch-spreadsheet',
    LaunchWebBrowser: 'launch-web-browser',
    LaunchWebCam: 'launch-web-cam',
    LaunchWordProcessor: 'launch-word-processor',
    LaunchApplication1: 'launch-application-1',
    LaunchApplication2: 'launch-application-2',
    LaunchApplication3: 'launch-application-3',
    LaunchApplication4: 'launch-application-4',
    LaunchApplication5: 'launch-application-5',
    LaunchApplication6: 'launch-application-6',
    LaunchApplication7: 'launch-application-7',
    LaunchApplication8: 'launch-application-8',
    LaunchApplication9: 'launch-application-9',
    LaunchApplication10: 'launch-application-10',
    LaunchApplication11: 'launch-application-11',
    LaunchApplication12: 'launch-application-12',
    LaunchApplication13: 'launch-application-13',
    LaunchApplication14: 'launch-application-14',
    LaunchApplication15: 'launch-application-15',
    LaunchApplication16: 'launch-application-16',

    // Browser
    BrowserBack: 'browser-back',
    BrowserFavorites: 'browser-favorites',
    BrowserForward: 'browser-forward',
    BrowserHome: 'browser-home',
    BrowserRefresh: 'browser-refresh',
    BrowserSearch: 'browser-search',
    BrowserStop: 'browser-stop',

    // Numeric keypad
    Decimal: 'decimal',
    Key11: 'key-11',
    Key12: 'key-12',
    Multiply: 'asterisk',
    Add: 'plus',
    Divide: 'slash',
    Subtract: 'minus',
    Separator: 'separator',
} as const;

const SPECIAL_INPUTS = {
    plus: '+',
    minus: '-',
    asterisk: '*',
    slash: '/',
    equal: '=',

    enter: '\n',
    tab: '\t',
    space: ' ',
    backspace: '\b',
    comma: ',',
    period: '.',
    semicolon: ';',
    'single-quote': "'",
    backquote: '`',
    backslash: '\\',
    'left-backslash': '\\',

    'bracket-left': '[',
    'bracket-right': ']',
} as const;

type ValueOf<T> = T[keyof T];

type HardwareKey = ValueOf<typeof HARDWARE_KEY_MAP>;
type SoftwareKey = ValueOf<typeof SOFTWARE_KEY_MAP>;
type ModifierKey = 'control' | 'alt' | 'shift' | 'meta';

type Key = {
    hardwareKey: HardwareKey;
    softwareKey: SoftwareKey;
    text: string;
};

type EncodedEvent = Key & {
    modifiers: ModifierKey[];
};

function encodeKey(event: KeyboardEvent): Key {
    let hardwareKey: HardwareKey;
    if (event.code in HARDWARE_KEY_MAP) {
        hardwareKey = HARDWARE_KEY_MAP[event.code];
    } else {
        console.warn(`Unknown hardware key code: ${event.code}`);
        hardwareKey = 'unknown';
    }

    let softwareKey: SoftwareKey;
    if (event.key in SOFTWARE_KEY_MAP) {
        softwareKey = SOFTWARE_KEY_MAP[event.key];
    } else if (event.key.length === 1) {
        softwareKey = event.key as SoftwareKey;
    } else {
        console.warn(`Unknown software key: ${event.key}`);
        softwareKey = 'unknown';
    }

    let text: string;
    if (event.key.length === 1) {
        text = event.key;
    } else {
        text = SPECIAL_INPUTS[softwareKey] ?? '';
    }

    return {
        hardwareKey: hardwareKey,
        softwareKey: softwareKey,
        text: text,
    };
}

function encodeEvent(event: KeyboardEvent): EncodedEvent {
    let modifiers: ModifierKey[] = [];

    if (event.altKey) {
        modifiers.push('alt');
    }

    if (event.ctrlKey) {
        modifiers.push('control');
    }

    if (event.shiftKey) {
        modifiers.push('shift');
    }

    if (event.metaKey) {
        modifiers.push('meta');
    }

    return {
        ...encodeKey(event),
        modifiers: modifiers,
    };
}

export type KeyEventListenerState = ComponentState & {
    _type_: 'KeyEventListener-builtin';
    content?: ComponentId;
    reportKeyDown?: boolean;
    reportKeyUp?: boolean;
    reportKeyPress?: boolean;
};

export class KeyEventListenerComponent extends SingleContainer {
    state: Required<KeyEventListenerState>;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.tabIndex = -1; // So that it can receive keyboard events
        return element;
    }

    updateElement(
        deltaState: KeyEventListenerState,
        latentComponents: Set<ComponentBase>
    ): void {
        let element = this.element;

        let reportKeyDown = firstDefined(
            deltaState.reportKeyDown,
            this.state.reportKeyDown
        );
        let reportKeyUp = firstDefined(
            deltaState.reportKeyUp,
            this.state.reportKeyUp
        );
        let reportKeyPress = firstDefined(
            deltaState.reportKeyPress,
            this.state.reportKeyPress
        );

        if (reportKeyDown || reportKeyPress) {
            element.onkeydown = (e: KeyboardEvent) => {
                let encodedEvent = encodeEvent(e);

                if (reportKeyPress) {
                    this.sendMessageToBackend({
                        type: 'KeyPress',
                        ...encodedEvent,
                    });
                }

                if (reportKeyDown && !e.repeat) {
                    this.sendMessageToBackend({
                        type: 'KeyDown',
                        ...encodedEvent,
                    });
                }
            };
        } else {
            element.onkeydown = null;
        }

        if (reportKeyUp) {
            element.onkeyup = (e: KeyboardEvent) => {
                this.sendMessageToBackend({
                    type: 'KeyUp',
                    ...encodeEvent(e),
                });
            };
        } else {
            element.onkeyup = null;
        }

        this.replaceOnlyChild(latentComponents, deltaState.content);
    }

    grabKeyboardFocus(): void {
        this.element.focus();
    }
}
