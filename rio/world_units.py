from dataclasses import KW_ONLY, dataclass
from typing import *  # type: ignore

# https://github.com/forgedsoftware/measurementcommon/blob/master/systems.json


SI_PREFIXES = (
    (24, "yotta", "Y"),
    (21, "zetta", "Z"),
    (18, "exa", "E"),
    (15, "peta", "P"),
    (12, "tera", "T"),
    (9, "giga", "G"),
    (6, "mega", "M"),
    (3, "kilo", "k"),
    (2, "hecto", "h"),
    (1, "deca", "da"),
    (-1, "deci", "d"),
    (-2, "centi", "c"),
    (-3, "milli", "m"),
    (-6, "micro", "μ"),
    (-9, "nano", "n"),
    (-12, "pico", "p"),
    (-15, "femto", "f"),
    (-18, "atto", "a"),
    (-21, "zepto", "z"),
    (-24, "yocto", "y"),
)


INFORMATION_PREFIXES = (
    (10, "kibi", "Ki"),
    (20, "mebi", "Mi"),
    (30, "gibi", "Gi"),
    (40, "tebi", "Ti"),
    (50, "pebi", "Pi"),
    (60, "exbi", "Ei"),
    (70, "zebi", "Zi"),
    (80, "yobi", "Yi"),
)


ALL_PREFIXES = SI_PREFIXES + INFORMATION_PREFIXES


@dataclass(frozen=True)
class Dimension:
    names: Sequence[str]
    _: KW_ONLY
    ampere: int = 0
    candela: int = 0
    kelvin: int = 0
    kilogram: int = 0
    metre: int = 0
    mole: int = 0
    second: int = 0
    bytes: int = 0

    def __mul__(self, other: "Dimension") -> "Dimension":
        return Dimension(
            tuple(),
            ampere=self.ampere + other.ampere,
            candela=self.candela + other.candela,
            kelvin=self.kelvin + other.kelvin,
            kilogram=self.kilogram + other.kilogram,
            metre=self.metre + other.metre,
            mole=self.mole + other.mole,
            second=self.second + other.second,
            bytes=self.bytes + other.bytes,
        )


# Base dimensions
ELECTRICAL_CURRENT = Dimension(("electrical current", "current"), ampere=1)
LUMINOSITY = Dimension(("luminosity",), candela=1)
TEMPERATURE = Dimension(("temperature",), kelvin=1)
MASS = Dimension(("mass", "weight", "tonnage"), kilogram=1)
LENGTH = Dimension(("length", "distance"), metre=1)
AMOUNT_OF_SUBSTANCE = Dimension(("amount of substance",), mole=1)
TIME = Dimension(("time", "duration"), second=1)
FILE_SIZE = Dimension(("file size",), bytes=1)

# Common derived dimensions
AREA = Dimension(("area",), metre=2)
VOLUME = Dimension(("volume",), metre=3)
SPEED = Dimension(("speed",), metre=1, second=-1)
ACCELERATION = Dimension(("acceleration",), metre=1, second=-2)
JERK = Dimension(("jerk",), metre=1, second=-3)
FORCE = Dimension(("force",), kilogram=1, metre=1, second=-2)
PRESSURE = Dimension(("pressure",), kilogram=1, metre=-1, second=-2)
ENERGY = Dimension(("energy",), kilogram=1, metre=2, second=-2)
POWER = Dimension(("power",), kilogram=1, metre=2, second=-3)
MOMENTUM = Dimension(("momentum",), kilogram=1, metre=2, second=-1)
FREQUENCY = Dimension(("frequency",), second=-1)


@dataclass(frozen=True)
class Unit:
    dimension: Dimension
    base_multiple: float
    prefixes: Sequence[tuple[int, str, str]]


AMPERE = Unit(ELECTRICAL_CURRENT, 1, SI_PREFIXES)
CANDELA = Unit(LUMINOSITY, 1, SI_PREFIXES)
KELVIN = Unit(TEMPERATURE, 1, SI_PREFIXES)
GRAM = Unit(MASS, 1e-3, SI_PREFIXES)
METRE = Unit(LENGTH, 1, SI_PREFIXES)
MOLE = Unit(AMOUNT_OF_SUBSTANCE, 1, SI_PREFIXES)
SECOND = Unit(TIME, 1, SI_PREFIXES)
BIT = Unit(FILE_SIZE, 1 / 8, INFORMATION_PREFIXES)
BYTE = Unit(FILE_SIZE, 1, INFORMATION_PREFIXES)


METRIC_TONNE = Unit(MASS, 1e3, SI_PREFIXES)
US_TON = Unit(MASS, 907.18474, ())
POUND = Unit(MASS, 0.45359237, ())
OUNCE = Unit(MASS, 0.028349523125, ())
STONE = Unit(MASS, 6.35029318, ())
GRAIN = Unit(MASS, 0.00006479891, ())
CARAT = Unit(MASS, 0.0002, ())

US_FOOT = Unit(LENGTH, 0.3048, ())
US_INCH = Unit(LENGTH, 0.0254, ())

US_MILE = Unit(LENGTH, 1609.344, ())
NAUTICAL_MILE = Unit(LENGTH, 1852, ())
LIGHT_YEAR = Unit(LENGTH, 9.4607304725808e15, ())
PARSEC = Unit(LENGTH, 3.0856775814914e16, ())
ANGSTROM = Unit(LENGTH, 1e-10, ())
ASTRONOMICAL_UNIT = Unit(LENGTH, 1.495978707e11, ())
