# Unit tests for the histogramming step
#
# Run from the repository root with: pytest -v
# Requires an environment with ROOT available

import ROOT
import pytest

import histograms


# Pytest runs every function named test_* and the test passes if no assert fails.

def test_ranges_are_valid():
    """
    Tests that the ranges are valid.
    """
    for variable, (nbins, low, high) in histograms.ranges.items():
        assert nbins > 0, f"{variable} has no bins"
        assert low < high, f"{variable} has an empty or inverted range"


def test_book_histogram():
    """
    Tests that the histogram is booked correctly.
    """
    # Build a small dataset in memory: 100 events with pt_1 = 30 GeV and unit weight, matching the columns
    # bookHistogram expects.
    df = ROOT.RDataFrame(100).Define("pt_1", "30.0").Define("weight", "1.0")
    h = histograms.bookHistogram(df, "pt_1", histograms.ranges["pt_1"])
    # Number of bins must be the same
    assert h.GetNbinsX() == histograms.ranges["pt_1"][0]
    # Entries must be the same as the number of events in the dataset
    assert h.GetEntries() == 100


# tmp_path is a built-in pytest fixture: each test gets a fresh temporary
# directory, so the test never touches real files and needs no cleanup.
def test_write_histogram(tmp_path):
    """
    Tests that the histogram is written correctly.
    """
    path = str(tmp_path / "output.root")
    tfile = ROOT.TFile(path, "RECREATE")
    h = ROOT.TH1D("original", "original", 10, 0, 1)
    histograms.writeHistogram(h, "renamed")
    tfile.Close()

    tfile = ROOT.TFile(path, "READ")
    assert tfile.Get("renamed"), "histogram not found under its new name"
    tfile.Close()


# parametrize runs the same test once per argument set. The dataset has 100
# events with gen_match alternating true/false, so ZTT and ZLL should each
# keep 50 events and any other process label should keep all 100.
@pytest.mark.parametrize(
    "label, expected_events",
    [("ZTT", 50), ("ZLL", 50), ("W", 100)],
)
def test_filter_gen_match(label, expected_events):
    """
    Tests that the filter gen match correctly.
    """
    df = ROOT.RDataFrame(100).Define("gen_match", "rdfentry_ % 2 == 0")
    filtered = histograms.filterGenMatch(df, label)
    assert filtered.Count().GetValue() == expected_events
