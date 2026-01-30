from balloon_sim.meteo.run_locator import GsmRun, build_open_gsm_1p25_upper_air_url


def test_open_url_builder_example() -> None:
    run = GsmRun(date_yyyymmdd="20260130", cycle_hh="00")
    base = "https://www.wis-jma.go.jp/d/o/RJTD/GRIB/"
    url = build_open_gsm_1p25_upper_air_url(base, run, fd_range="FD0000-0512")
    assert "Global_Spectral_Model/Latitude_Longitude/1.25_1.25" in url
    assert "Upper_air_layers/20260130/000000" in url
    assert "C_RJTD_20260130000000" in url
    assert url.endswith("FD0000-0512_grib2.bin")
