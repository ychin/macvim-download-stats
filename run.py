#!/usr/bin/env python3

# Query GitHub release API and Homebrew formula stats to track MacVim's
# downloads over time, as those APIs only provide a snapshot rather than
# download/install count history.
#
# Store the output in CSV files to make them easy to import to other tools.
#
# Note: This file needs Python 3.11+ to get the more flexible
# datetime.fromisoformat() implementation. If we have to run on 3.10 or below,
# we could add the dateutil package as a dependency.

from datetime import datetime, timezone
from urllib.request import Request, urlopen
import csv
import json
import os
import os.path
import sys

if sys.version_info.major == 3 and sys.version_info.minor <= 10:
    # We need Python 3.11 to run properly. See notes section above.
    print(f'Python version is too old (need to be 3.11+): {sys.version}', file=sys. stderr)
    exit(-100)

utc_date_header = "Date (UTC)"

# Extract the current UTC time, and store in a sort-of ISO format. Don't use
# the official YYYY-MM-DDTHH:MM:SS format or add timezone info, because those
# will confuse Excel or Google Spreadsheets during import as those tools don't
# have good date/time support.
now_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def query_github_releases():
    # Using GitHub Token is optional as releases is public. Using a token helps prevent rate limiting.
    gh_token = os.environ.get("GITHUB_TOKEN")

    # Query the GitHub releases API: https://docs.github.com/en/rest/releases/releases
    request = Request(url="https://api.github.com/repos/macvim-dev/macvim/releases")
    if gh_token != None:
        request.add_header("Authorization", f"Bearer {gh_token}")
    response = urlopen(request)

    releases = json.loads(response.read())

    first_item = True

    # Release info to gather in a separate table
    new_release_rows = []
    release_columns = [
        "id",
        "tag_name",
        "name",
        "draft",
        "prerelease",
        "created_at",
        "published_at",
    ]

    # Loop through all releases
    for release in releases:
        # Gather release info, and fix up date time to be spreadsheet parsable
        release_row = {c: release[c] for c in release_columns}
        for field in ["created_at", "published_at"]:
            release_row[field] = (
                datetime.fromisoformat(release_row[field])
                .astimezone(timezone.utc)
                .strftime("%Y-%m-%d %H:%M:%S")
            )
        new_release_rows.append(release_row)

        # Add a row of download counts for each asset to the CSV. Make the CSV file
        # if it doesn't exist. If one is already there, parses it to make sure the
        # header matches the assets we have. The logic here is slightly complicated
        # just to make sure if we added/removed assets from this release, the
        # column order will still make sense.

        release_csv_path = os.path.join(
            "github_release/downloads", f'{release["tag_name"]}.csv'
        )
        release_json_path = os.path.join(
            "github_release/info", f'{release["tag_name"]}.json'
        )
        new_release_csv = not os.path.exists(release_csv_path)

        asset_names = [asset["name"] for asset in release["assets"]]
        if len(asset_names) == 0:
            continue

        existing_rows = []  # Only used when need to convert CSV file

        if new_release_csv:
            os.makedirs(os.path.dirname(release_csv_path), exist_ok=True)
            with open(release_csv_path, "w", newline="") as release_csv_file:
                writer = csv.writer(release_csv_file)
                writer.writerow([utc_date_header] + asset_names)
        else:
            with open(release_csv_path, "r", newline="") as release_csv_file:
                reader = csv.DictReader(release_csv_file)
                header = reader.fieldnames
                if reader.fieldnames == None:
                    print(f"Found csv file with no headers: {release_csv_path}")
                    exit(-1)

                old_asset_names = reader.fieldnames[1:]
                old_asset_names_set = set(old_asset_names)

                new_asset_names = [
                    n for n in asset_names if n not in old_asset_names_set
                ]
                asset_names = old_asset_names + [
                    n for n in asset_names if n not in old_asset_names_set
                ]

                if len(new_asset_names) > 0:
                    # We have added new assets to this release. We need to convert
                    # the CSV file because we need to change the header, which also
                    # means we need to read the rest of the file so we can write
                    # them back later.
                    print(
                        f'Release {release["tag_name"]} added assets f{new_asset_names}. Converting CSV file.'
                    )
                    existing_rows = [row for row in reader]

        # We only append to the end of the file unless we have added assets forcing
        # us to re-write the header.
        file_mode = "w" if len(existing_rows) > 0 else "a"

        with open(release_csv_path, file_mode, newline="") as release_csv_file:
            writer = csv.DictWriter(
                release_csv_file, fieldnames=[utc_date_header] + asset_names
            )

            if len(existing_rows) > 0:
                writer.writeheader()
                writer.writerows(existing_rows)

            row = {
                name: download_count
                for (name, download_count) in [
                    (asset["name"], asset["download_count"])
                    for asset in release["assets"]
                ]
            }

            if first_item:
                print("  " + str(row))

            row[utc_date_header] = now_time
            writer.writerow(row)

        # Also write out the release's JSON just for reference instead of needing query GitHub in the future
        os.makedirs(os.path.dirname(release_json_path), exist_ok=True)
        with open(release_json_path, "w") as release_json_file:
            json.dump(release, release_json_file, indent=2)

        first_item = False

    # Output the releases info into its own table so we can look up metadata like publish date etc
    releases_info_csv_path = "github_release/releases.csv"
    if os.path.exists(releases_info_csv_path):
        with open(releases_info_csv_path, "r", newline="") as releases_info_file:
            reader = csv.DictReader(releases_info_file)
            old_release_rows = [row for row in reader]

        old_release_ids = {release["id"] for release in old_release_rows}

        release_rows = old_release_rows
        release_rows += [r for r in new_release_rows if str(r['id']) not in old_release_ids]
    else:
        release_rows = new_release_rows

    release_rows = sorted(release_rows, key = lambda o: o['id'])

    with open(releases_info_csv_path, "w", newline="") as releases_info_file:
        writer = csv.DictWriter(releases_info_file, fieldnames=release_columns)
        writer.writeheader()
        writer.writerows(release_rows)


def query_homebrew_installs():
    response = urlopen("https://formulae.brew.sh/api/formula/macvim.json")
    formula_info = json.loads(response.read())

    generated_date = formula_info["generated_date"]
    version = formula_info["versions"]["stable"]
    num_installs = formula_info["analytics"]["install"]["30d"]["macvim"]
    num_installs_on_request = formula_info["analytics"]["install_on_request"]["30d"][
        "macvim"
    ]

    csv_path = os.path.join("homebrew", "installs.csv")

    if not os.path.exists(csv_path):
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        with open(csv_path, "w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [
                    utc_date_header,
                    "generated_date",
                    "versions.stable",
                    "install.30d",
                    "install_on_request.30d",
                ]
            )

    with open(csv_path, "a", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [now_time, generated_date, version, num_installs, num_installs_on_request]
        )

    print(
        f"  num_installs: {num_installs}, num_installs_on_request: {num_installs_on_request}, version: {version}"
    )


if __name__ == "__main__":
    print("Querying GitHub release stats.")
    query_github_releases()

    print("Querying Homebrew install stats.")
    query_homebrew_installs()
