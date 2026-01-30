from balloon_sim.meteo.run_locator import fd_code


def test_fd_code_examples() -> None:
    assert fd_code(0) == "FD0000"
    assert fd_code(132) == "FD0512"  # 5 days 12 hours
    assert fd_code(264) == "FD1100"  # 11 days 0 hours
