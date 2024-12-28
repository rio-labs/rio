"""
Parses various user agents, making sure the parsed information is correct.
"""

import pytest

import rio.utils


@pytest.mark.parametrize(
    "user_agent_string, os_name, browser_name, browser_engine, device_type",
    [
        # Invalid user agent strings
        #
        # These are incredible feats of my own imagination.
        [
            "",
            "unknown",
            "unknown",
            "unknown",
            "unknown",
        ],
        [
            "totally/made up user///agent",
            "unknown",
            "unknown",
            "unknown",
            "unknown",
        ],
        [
            "Mozilla/5.0 (MyOsIsBetterThanUrs) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.3",
            "unknown",
            "Chrome",
            "chrome",
            "desktop",
        ],
        [
            "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/27.0 Foobar Mobile Safari/537.3",
            "unknown",
            "Foobar",
            "unknown",
            "desktop",
        ],
        # Valid user agent strings
        #
        # These were taken from https://useragents.me/ on 2024-12-28.
        (
            "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.3",
            "Android",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1.1 Mobile/15E148 Safari/604.",
            "iOS",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/27.0 Chrome/125.0.0.0 Mobile Safari/537.3",
            "Android",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) GSA/346.1.704810410 Mobile/15E148 Safari/604.",
            "iOS",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.",
            "iOS",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/131.0.6778.134 Mobile/15E148 Safari/604.",
            "iOS",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36 OPR/86.0.0.",
            "Android",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (Linux; Android 11; moto e20 Build/RONS31.267-94-14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.135 Mobile Safari/537.3",
            "Android",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.3",
            "Android",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (Android 13; Mobile; rv:133.0) Gecko/133.0 Firefox/133.",
            "Android",
            "Firefox",
            "firefox",
            "phone",
        ),
        (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0.1 Mobile/15E148 Safari/604.",
            "iOS",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.",
            "iOS",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 18_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Mobile/15E148 Safari/604.",
            "iOS",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.3",
            "Android",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (Linux; arm_64; Android 15; 24030PN60G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.98 YaBrowser/24.12.1.98.00 SA/3 Mobile Safari/537.3",
            "Android",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (Linux; Android 7.0; SM-G930V Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.125 Mobile Safari/537.36 (compatible; Google-Read-Aloud; +https://support.google.com/webmasters/answer/1061943",
            "Android",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (Linux; Android 13; M2103K19G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Mobile Safari/537.3",
            "Android",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (Linux; Android 12; 220733SG Build/SP1A.210812.016) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.135 Mobile Safari/537.3",
            "Android",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (Linux; Android 11; moto e20 Build/RONS31.267-94-14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.105 Mobile Safari/537.3",
            "Android",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (Linux; Android 10; SAMSUNG SM-G980F) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/22.0 Chrome/111.0.5563.116 Mobile Safari/537.3",
            "Android",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (Linux; Android 10; NEN-LX1 Build/HUAWEINEN-LX1; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.105 Mobile Safari/537.36 HuaweiBrowser/15.0.4.312 HMSCore/6.14.0.32",
            "Android",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/25.0 Chrome/121.0.0.0 Mobile Safari/537.3",
            "Android",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.3",
            "Android",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.3",
            "Android",
            "Chrome",
            "chrome",
            "phone",
        ),
        (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.1",
            "macOS",
            "Chrome",
            "chrome",
            "desktop",
        ),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.3",
            "Windows",
            "Chrome",
            "chrome",
            "desktop",
        ),
        (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.3",
            "macOS",
            "Chrome",
            "chrome",
            "desktop",
        ),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.",
            "Windows",
            "Firefox",
            "firefox",
            "desktop",
        ),
        (
            "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.",
            "Windows",
            "Firefox",
            "firefox",
            "desktop",
        ),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.",
            "Windows",
            "Chrome",
            "chrome",
            "desktop",
        ),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Herring/97.1.8280.8",
            "Windows",
            "Chrome",
            "chrome",
            "desktop",
        ),
        (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.3",
            "Linux",
            "Chrome",
            "chrome",
            "desktop",
        ),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 OPR/115.0.0.",
            "Windows",
            "Chrome",
            "chrome",
            "desktop",
        ),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 AtContent/95.5.5462.5",
            "Windows",
            "Chrome",
            "chrome",
            "desktop",
        ),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.1958",
            "Windows",
            "Chrome",
            "chrome",
            "desktop",
        ),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.3",
            "Windows",
            "Chrome",
            "chrome",
            "desktop",
        ),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 OPR/114.0.0.",
            "Windows",
            "Chrome",
            "chrome",
            "desktop",
        ),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.3",
            "Windows",
            "Chrome",
            "chrome",
            "desktop",
        ),
    ],
)
def test_parse_user_agent(
    user_agent_string: str,
    os_name: str,
    browser_name: str,
    browser_engine: str,
    device_type: str,
) -> None:
    # Get information from the user agent string
    (
        parsed_os_name,
        parsed_browser_name,
        parsed_browser_engine,
        parsed_device_type,
    ) = rio.utils.parse_system_information_from_user_agent(user_agent_string)

    # Verify the parsed information is correct
    assert parsed_os_name == os_name
    assert parsed_browser_name == browser_name
    assert parsed_browser_engine == browser_engine
    assert parsed_device_type == device_type


# rio.utils.parse_system_information_from_user_agent(
#     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.3",
# )
