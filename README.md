# MacVim downloads / installs statistics query tool

[![MacVim download stats](https://github.com/ychin/macvim-download-stats/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/ychin/macvim-download-stats/actions/workflows/ci.yaml)

Repository to query GitHub release and Homebrew install statistics to track MacVim download count over time. The reason why this exists is that those APIs only provide a snapshot of the current download count, which makes it hard to track installation patterns over time. This is useful for estimating number of actual uses of the software and how fast users upgrade to new versions once released.

Currently the output is stored in CSV files in a separate "download-stats" branch, but there are no web visualization provided for now. Simply import them to a spreadsheet program.
