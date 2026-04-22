import pytest
from social_media_engagement_engine import EngagementEngine

def test_init_defaults():
    engine = EngagementEngine("user123")
    assert engine.user_handle == "user123"
    assert engine.score == 0.0
    assert engine.verified is False

def test_init_verified_true():
    engine = EngagementEngine("creator1", verified=True)
    assert engine.user_handle == "creator1"
    assert engine.score == 0.0
    assert engine.verified is True

@pytest.mark.parametrize(
    "itype,count,verified,expected_score",
    [
        ("like", 1, False, 1.0),
        ("comment", 1, False, 5.0),
        ("share", 1, False, 10.0),
        ("like", 3, False, 3.0),
        ("comment", 2, False, 10.0),
        ("share", 4, False, 40.0),
        ("like", 2, True, 3.0),
        ("comment", 2, True, 15.0),
        ("share", 2, True, 30.0),
        ("like", 0, False, 0.0),
    ],
)

def test_process_interaction_valid_cases(itype, count, verified, expected_score):
    engine = EngagementEngine("user123", verified=verified)
    result = engine.process_interaction(itype, count)
    assert result is True
    assert engine.score == pytest.approx(expected_score)

def test_process_interaction_invalid_type_returns_false():
    engine = EngagementEngine("user123")
    result = engine.process_interaction("follow", 5)
    assert result is False
    assert engine.score == 0.0

def test_process_interaction_negative_count_raises_value_error():
    engine = EngagementEngine("user123")
    with pytest.raises(ValueError, match="Negative count"):
        engine.process_interaction("like", -1)

def test_score_accumulates_across_multiple_calls():
    engine = EngagementEngine("user123")

    engine.process_interaction("like", 10)      # 10
    engine.process_interaction("comment", 2)    # 10
    engine.process_interaction("share", 1)      # 10
    assert engine.score == pytest.approx(30.0)


def test_verified_score_accumulates_across_multiple_calls():
    engine = EngagementEngine("creator1", verified=True)

    engine.process_interaction("like", 2)       # 3
    engine.process_interaction("comment", 2)    # 15
    engine.process_interaction("share", 1)      # 15
    assert engine.score == pytest.approx(33.0)


@pytest.mark.parametrize(
    "score,expected_tier",
    [
        (0.0, "Newbie"),
        (99.99, "Newbie"),
        (100.0, "Influencer"),
        (500.0, "Influencer"),
        (1000.0, "Influencer"),
        (1000.01, "Icon"),
    ],
)
def test_get_tier_boundaries(score, expected_tier):
    engine = EngagementEngine("user123")
    engine.score = score

    assert engine.get_tier() == expected_tier


def test_apply_penalty_reduces_score():
    engine = EngagementEngine("user123")
    engine.score = 200.0
    engine.apply_penalty(2)   # 40% reduction = 80
    assert engine.score == pytest.approx(120.0)


def test_apply_penalty_zero_reports_does_not_change_score():
    engine = EngagementEngine("user123")
    engine.score = 200.0
    engine.apply_penalty(0)
    assert engine.score == pytest.approx(200.0)

def test_apply_penalty_caps_score_at_zero():
    engine = EngagementEngine("user123")
    engine.score = 50.0
    engine.apply_penalty(10)  # 200% reduction
    assert engine.score == 0


def test_apply_penalty_above_10_removes_verification():
    engine = EngagementEngine("creator1", verified=True)
    engine.score = 500.0
    engine.apply_penalty(11)
    assert engine.verified is False


def test_apply_penalty_at_10_does_not_remove_verification():
    engine = EngagementEngine("creator1", verified=True)
    engine.score = 500.0
    engine.apply_penalty(10)
    assert engine.verified is True

def test_apply_penalty_above_10_still_reduces_score():
    engine = EngagementEngine("creator1", verified=True)
    engine.score = 500.0
    engine.apply_penalty(11)  # 220% reduction, should floor at 0
    assert engine.score == 0
    assert engine.verified is False