from evidentia.scanners.github import scan_github_fixture
from evidentia.scanners.hn import scan_hn_fixture
from evidentia.scanners.reddit import scan_reddit_fixture


FIXTURE_SCANNERS = {
    "github": scan_github_fixture,
    "hn": scan_hn_fixture,
    "reddit": scan_reddit_fixture,
}
