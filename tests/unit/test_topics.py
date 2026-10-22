from alphaxiv._topics import search_topics


def test_topics_match_codes_and_normalized_labels() -> None:
    assert search_topics("CS.LG") == ["machine-learning"]
    assert search_topics("Agentic") == ["agentic-frameworks"]
    assert search_topics("reinforcement_learning") == [
        "reinforcement-learning",
        "deep-reinforcement-learning",
    ]


def test_topics_empty_unknown_and_duplicate_labels() -> None:
    assert search_topics("   ") == []
    assert search_topics("no-such-topic-xyz") == []
    assert search_topics("mathematical physics").count("mathematical-physics") == 1
