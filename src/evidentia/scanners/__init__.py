from evidentia.scanners.hn import scan_hn_fixture, scan_hn_live
from evidentia.scanners.reddit import scan_reddit_fixture, scan_reddit_live
from evidentia.scanners.github import scan_github_fixture, scan_github_live


FIXTURE_SCANNERS = {
    "hn": scan_hn_fixture,
    "reddit": scan_reddit_fixture,
    "github": scan_github_fixture,
}

LIVE_SCANNERS = {
    "hn": scan_hn_live,
    "reddit": scan_reddit_live,
    "github": scan_github_live,
}
