from relaycoord import analyze_study, coordinated_feeder, miscoordinated_feeder


def test_coordinated_worked_case_passes():
    result = analyze_study(coordinated_feeder())
    assert result.all_coordinated
    assert all(pair.margin_s >= 0.30 for pair in result.coordination_pairs)


def test_miscoordinated_worked_case_flags_pairs():
    result = analyze_study(miscoordinated_feeder())
    assert not result.all_coordinated
    assert any(not pair.coordinated for pair in result.coordination_pairs)


def test_relay_order_is_downstream_to_upstream():
    result = analyze_study(coordinated_feeder())
    times = [relay.operating_time_s for relay in result.relay_results]
    assert times == sorted(times)
