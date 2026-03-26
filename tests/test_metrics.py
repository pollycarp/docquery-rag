"""
Phase 4 Tests — Evaluation Metrics
"""

from evaluation.metrics import hit_rate, reciprocal_rank, exact_match, citation_present, compute_summary


# ── Hit Rate ──────────────────────────────────────────────────────────────────

def test_hit_rate_true_when_phrase_found():
    contents = ["Employees get 10 days of paid sick leave per year.", "Other content."]
    assert hit_rate(contents, ["10 days of paid sick leave"]) is True


def test_hit_rate_false_when_phrase_not_found():
    contents = ["Annual leave is 20 days.", "Remote work requires VPN."]
    assert hit_rate(contents, ["sick leave"]) is False


def test_hit_rate_case_insensitive():
    contents = ["EMPLOYEES GET 10 DAYS OF PAID SICK LEAVE"]
    assert hit_rate(contents, ["10 days of paid sick leave"]) is True


# ── MRR ───────────────────────────────────────────────────────────────────────

def test_reciprocal_rank_first_position():
    contents = ["10 days of paid sick leave", "other chunk", "another chunk"]
    assert reciprocal_rank(contents, ["10 days of paid sick leave"]) == 1.0


def test_reciprocal_rank_second_position():
    contents = ["irrelevant chunk", "10 days of paid sick leave", "another"]
    assert reciprocal_rank(contents, ["10 days of paid sick leave"]) == 0.5


def test_reciprocal_rank_zero_when_not_found():
    contents = ["nothing relevant here", "still nothing"]
    assert reciprocal_rank(contents, ["sick leave"]) == 0.0


# ── Exact Match ───────────────────────────────────────────────────────────────

def test_exact_match_true():
    assert exact_match("You are entitled to 10 days of sick leave.", "10 days") is True


def test_exact_match_false():
    assert exact_match("You are entitled to annual leave.", "sick leave") is False


def test_exact_match_case_insensitive():
    assert exact_match("According to the policy, TEN DAYS is the entitlement.", "ten days") is True


# ── Citation ──────────────────────────────────────────────────────────────────

def test_citation_present_true():
    assert citation_present("According to sample_policy.txt...", "sample_policy.txt") is True


def test_citation_present_false():
    assert citation_present("The answer is 10 days.", "sample_policy.txt") is False


# ── Summary ───────────────────────────────────────────────────────────────────

def test_compute_summary_averages_correctly():
    results = [
        {"hit": True,  "reciprocal_rank": 1.0, "exact_match": True,  "citation_present": True},
        {"hit": False, "reciprocal_rank": 0.0, "exact_match": False, "citation_present": False},
    ]
    summary = compute_summary(results)
    assert summary["hit_rate"]         == 0.5
    assert summary["mrr"]              == 0.5
    assert summary["exact_match_rate"] == 0.5
    assert summary["citation_rate"]    == 0.5
    assert summary["total_questions"]  == 2


def test_compute_summary_empty_returns_empty():
    assert compute_summary([]) == {}
