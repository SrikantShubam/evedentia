from evidentia.scanners.github import scan_github_fixture, scan_github_live
from evidentia.scanners.hn import scan_hn_fixture
from evidentia.scanners.reddit import scan_reddit_fixture, scan_reddit_live


FIXTURE_SCANNERS = {
    "github": scan_github_fixture,
    "hn": scan_hn_fixture,
    "reddit": scan_reddit_fixture,
}

LIVE_SCANNERS = {
    "github": scan_github_live,
    "hn": None,
    "reddit": scan_reddit_live,
}
