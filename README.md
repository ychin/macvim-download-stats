# MacVim downloads / installs statistics query tool

[![MacVim download stats](https://github.com/ychin/macvim-download-stats/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/ychin/macvim-download-stats/actions/workflows/ci.yaml)

Repository to query GitHub release and Homebrew install statistics to track MacVim download count over time. The reason why this exists is that those APIs only provide a snapshot of the current download count, which makes it hard to track installation patterns over time. These patterns are useful for estimating number of actual users of the software and how fast users upgrade to new versions once released. For example, it would be interesting to compare the download trends of delta asset (only used by the updater to upgrade to a new version) versus a full dmg file (either a full download from the web page or used by the updater as a fallback). For Homebrew it's also useful to see how fast users update to the version of software, as that involves a manual step from the user.

This is run by GitHub Actions automatically. The output is commited to a separate "download-stats" branch.

Currently the output is stored in CSV files storing the raw download count data. CSV is used for simplicity and ease of import for other tools. This tool is not generating a visualziation web page for now, but that could be added in the future. The simplest way to use the output is to create a Google Spreadsheet to aggregate the data. The raw data from this repo's output can be used directly (and kept up-to-date) by using the [IMPORTDATA](https://support.google.com/docs/answer/3093335) function. Example:

    =IMPORTDATA("https://raw.githubusercontent.com/ychin/macvim-download-stats/download-stats/github_release/downloads/release-176.csv")

