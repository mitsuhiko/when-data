import os
import click
from collections import namedtuple


Location = namedtuple(
    "Location",
    [
        "name",
        "aliases",
        "country",
        "admin_code",
        "kind",
        "tz",
        "geoid",
        "sort_key",
    ],
)


DATA_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "dump")

# geonames
GEONAMEID = 0
NAME = 1
ASCIINAME = 2
ALTERNATENAMES = 3
LATITUDE = 4
LONGITUDE = 5
FEATURE_CLASS = 6
FEATURE_CODE = 7
COUNTRY_CODE = 8
CC2 = 9
ADMIN1_CODE = 10
ADMIN2_CODE = 11
ADMIN3_CODE = 12
ADMIN4_CODE = 13
POPULATION = 14
ELEVATION = 15
DEM = 16
TIMEZONE = 17
MODIFICATION_DATE = 18

# alt names
AN_ALTERNATENAMEID = 0
AN_GEONAMEID = 1
AN_ISOLANGUAGE = 2
AN_ALTERNATE_NAME = 3
AN_ISPREFERREDNAME = 4
AN_ISSHORTNAME = 5
AN_ISCOLLOQUIAL = 6
AN_ISHISTORIC = 7
AN_FROM = 8
AN_TO = 9

# country info
CI_ISO = 0
CI_ISO3 = 1
CI_ISO_NUMERIC = 2
CI_FIPS = 3
CI_COUNTRY = 4
CI_CAPITAL = 5
CI_AREA = 6
CI_POPULATION = 7
CI_CONTINENT = 8
CI_TLD = 9
CI_CURRENCYCODE = 10
CI_CURRENCYNAME = 11
CI_PHONE = 12
CI_POSTAL_CODE_FORMAT = 13
CI_POSTAL_CODE_REGEX = 14
CI_LANGUAGES = 15
CI_GEONAMEID = 16
CI_NEIGHBOURS = 17
CI_EQUIVALENTFIPSCODE = 18

memoized = {}


def find_locations():
    locations = []
    potential_locations = {}

    def memoize_str(name_bytes):
        rv = memoized.get(name_bytes)
        if rv is None:
            rv = name_bytes.decode("utf-8")
            memoized[name_bytes] = rv
        return rv

    def get_airport_aliases(pieces):
        alt_names = pieces[ALTERNATENAMES].split(b",")
        return [
            x.decode("utf-8")
            for x in alt_names
            if len(x) == 3 and x.isalpha() and x.isupper()
        ]

    length = os.path.getsize(os.path.join(DATA_PATH, "allCountries.txt"))
    with open(os.path.join(DATA_PATH, "allCountries.txt"), "rb") as f:
        with click.progressbar(
            length=length, label="[1] Finding locations", update_min_steps=1000
        ) as pb:
            for idx, line in enumerate(f):
                pb.update(len(line))
                line = line.rstrip()
                if line.startswith(b"#"):
                    continue
                pieces = line.split(b"\t")
                feature_code = pieces[FEATURE_CODE]
                definite_location = True
                aliases = []
                if feature_code == b"AIRP":
                    aliases = get_airport_aliases(pieces)
                    if not aliases:
                        continue
                    kind = "airport"
                elif feature_code in (b"PPLA", b"PPLC") or (
                    feature_code[:1] == b"P" and int(pieces[POPULATION]) >= 50000
                ):
                    kind = "city"
                elif feature_code == b"ADM1" or (
                    feature_code == b"ADM2" and pieces[COUNTRY_CODE] == b"US"
                ):
                    kind = "division"
                    definite_location = False
                else:
                    continue

                geoid = int(pieces[GEONAMEID].decode("utf-8"))
                admin_code = pieces[ADMIN1_CODE]
                if admin_code.isalpha():
                    admin_code = memoize_str(admin_code)
                else:
                    admin_code = None

                loc = Location(
                    name=pieces[ASCIINAME].decode("utf-8"),
                    aliases=aliases,
                    country=memoize_str(pieces[COUNTRY_CODE]),
                    admin_code=admin_code,
                    kind=kind,
                    tz=memoize_str(pieces[TIMEZONE]),
                    geoid=geoid,
                    sort_key=(
                        pieces[FEATURE_CODE] != b"PPLC",
                        pieces[COUNTRY_CODE] != b"US",
                        -int(pieces[POPULATION].decode("utf-8")),
                    ),
                )
                if definite_location:
                    locations.append(loc)
                else:
                    potential_locations[loc.geoid] = loc

    length = os.path.getsize(os.path.join(DATA_PATH, "alternateNamesV2.txt"))
    with open(os.path.join(DATA_PATH, "alternateNamesV2.txt"), "rb") as f:
        with click.progressbar(
            length=length, label="[2] Finding alternative names", update_min_steps=1000
        ) as pb:
            for line in f:
                pb.update(len(line))
                line = line.rstrip()
                if line.startswith(b"#"):
                    continue
                pieces = line.split(b"\t")
                if pieces[AN_ISOLANGUAGE] != b"en":
                    continue
                geoid = int(pieces[AN_GEONAMEID].decode("utf-8"))
                loc = potential_locations.get(geoid)
                if loc is not None:
                    loc.aliases.append(pieces[AN_ALTERNATE_NAME].decode("utf-8"))

    for loc in potential_locations.values():
        if loc.aliases:
            locations.append(loc)

    locations.sort(key=lambda x: x.sort_key)
    return locations


def get_countries():
    rv = {}
    with open(os.path.join(DATA_PATH, "countryInfo.txt"), "rb") as f:
        for line in f:
            line = line.strip()
            if line.startswith(b"#"):
                continue
            pieces = line.decode("utf-8").split("\t")
            rv[pieces[CI_ISO]] = pieces[CI_COUNTRY]
    return rv


def serialize(value):
    if value is None:
        return ""
    elif isinstance(value, list):
        return ";".join(value)
    return str(value)


@click.command()
def main():
    locations = find_locations()
    click.echo("[3] Writing locations")
    with open("locations.txt", "w") as f:
        for loc in locations:
            f.write("\t".join(map(serialize, loc[:-2])) + "\n")
    click.echo("[4] Writing countries")
    with open("countries.txt", "w") as f:
        for code, country in sorted(get_countries().items()):
            f.write("\t".join([code, country]) + "\n")


if __name__ == "__main__":
    main()
