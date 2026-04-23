import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "afip_live: mark test as requiring real AFIP SDK credentials (skip in CI)",
    )


def pytest_collection_modifyitems(config, items):
    skip_live = pytest.mark.skip(reason="requires AFIP credentials; run with --afip-live")
    for item in items:
        if "afip_live" in item.keywords and not config.getoption("--afip-live", default=False):
            item.add_marker(skip_live)


def pytest_addoption(parser):
    parser.addoption(
        "--afip-live",
        action="store_true",
        default=False,
        help="Run tests that hit real AFIP/ARCA endpoints",
    )
