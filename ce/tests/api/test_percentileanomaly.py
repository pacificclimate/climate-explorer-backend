from ce.api import percentileanomaly
import pytest
import werkzeug
import math

default_region = "bc"
default_climatology = "2080"
default_variable = "tasmean"

default_response = {
    "anomaly": [
        {
            "timescale": "monthly",
            "date": "2085-01-15 00:00:00",
            "values": [5.9609112305751175],
        },
        {
            "timescale": "monthly",
            "date": "2085-02-15 00:00:00",
            "values": [4.8912718845794325],
        },
        {
            "timescale": "monthly",
            "date": "2085-03-15 00:00:00",
            "values": [4.982531268998228],
        },
        {
            "timescale": "monthly",
            "date": "2085-04-15 00:00:00",
            "values": [4.986594162466328],
        },
        {
            "timescale": "monthly",
            "date": "2085-05-15 00:00:00",
            "values": [5.171321292230795],
        },
        {
            "timescale": "monthly",
            "date": "2085-06-15 00:00:00",
            "values": [4.731830514637421],
        },
        {
            "timescale": "monthly",
            "date": "2085-07-15 00:00:00",
            "values": [5.784998484540889],
        },
        {
            "timescale": "monthly",
            "date": "2085-08-15 00:00:00",
            "values": [4.953678662970022],
        },
        {
            "timescale": "monthly",
            "date": "2085-09-15 00:00:00",
            "values": [5.049418130686874],
        },
        {
            "timescale": "monthly",
            "date": "2085-10-15 00:00:00",
            "values": [3.8691740413019957],
        },
        {
            "timescale": "monthly",
            "date": "2085-11-15 00:00:00",
            "values": [5.96149330599915],
        },
        {
            "timescale": "monthly",
            "date": "2085-12-15 00:00:00",
            "values": [6.09001669819771],
        },
        {
            "timescale": "seasonal",
            "date": "2085-01-16 00:00:00",
            "values": [5.672116408712057],
        },
        {
            "timescale": "seasonal",
            "date": "2085-04-16 00:00:00",
            "values": [5.156124457493562],
        },
        {
            "timescale": "seasonal",
            "date": "2085-07-16 00:00:00",
            "values": [5.356596218201004],
        },
        {
            "timescale": "seasonal",
            "date": "2085-10-16 00:00:00",
            "values": [4.7972872718649],
        },
        {
            "timescale": "yearly",
            "date": "2085-07-02 00:00:00",
            "values": [5.354819159523576],
        },
    ],
    "baseline": [
        {
            "timescale": "monthly",
            "date": "1977-01-15 00:00:00",
            "values": "-11.71985179823703",
        },
        {
            "timescale": "monthly",
            "date": "1977-02-15 00:00:00",
            "values": "-8.14627567484382",
        },
        {
            "timescale": "monthly",
            "date": "1977-03-15 00:00:00",
            "values": "-4.646276537509149",
        },
        {
            "timescale": "monthly",
            "date": "1977-04-15 00:00:00",
            "values": "0.7666356861442729",
        },
        {
            "timescale": "monthly",
            "date": "1977-05-15 00:00:00",
            "values": "5.834395942409077",
        },
        {
            "timescale": "monthly",
            "date": "1977-06-15 00:00:00",
            "values": "9.987749192375146",
        },
        {
            "timescale": "monthly",
            "date": "1977-07-15 00:00:00",
            "values": "12.493244837012119",
        },
        {
            "timescale": "monthly",
            "date": "1977-08-15 00:00:00",
            "values": "11.95668687759326",
        },
        {
            "timescale": "monthly",
            "date": "1977-09-15 00:00:00",
            "values": "7.598367298839455",
        },
        {
            "timescale": "monthly",
            "date": "1977-10-15 00:00:00",
            "values": "2.206109545491112",
        },
        {
            "timescale": "monthly",
            "date": "1977-11-15 00:00:00",
            "values": "-6.0411139425435305",
        },
        {
            "timescale": "monthly",
            "date": "1977-12-15 00:00:00",
            "values": "-10.544506796504631",
        },
        {
            "timescale": "seasonal",
            "date": "1977-01-16 00:00:00",
            "values": "-10.197912446193756",
        },
        {
            "timescale": "seasonal",
            "date": "1977-04-16 00:00:00",
            "values": "0.6503344819899319",
        },
        {
            "timescale": "seasonal",
            "date": "1977-07-16 00:00:00",
            "values": "11.495438686239407",
        },
        {
            "timescale": "seasonal",
            "date": "1977-10-16 00:00:00",
            "values": "1.264912051486151",
        },
        {
            "timescale": "yearly",
            "date": "1977-07-02 00:00:00",
            "values": "0.8551423608977357",
        },
    ],
    "baseline_climatology": "6190",
    "baseline_model": "anusplin",
    "climatology": "2080",
    "percentiles": [50.0],
    "region": "bc",
    "units": "degC",
    "variable": "tasmean",
}


@pytest.mark.parametrize("region, exists", [("bc", True), ("fake_region", False)])
def test_percentile_anomaly_regions(populateddb_session, region, exists):
    sesh = populateddb_session
    if exists:
        percentileanomaly(sesh, region, default_climatology, default_variable)
    else:
        with pytest.raises(werkzeug.exceptions.NotFound):
            assert default_response == percentileanomaly(
                sesh, region, default_climatology, default_variable
            )


@pytest.mark.parametrize("bmodel", ["anusplin", "fake_model", ""])
@pytest.mark.parametrize("bclimatology", ["6190", "3000", ""])
def test_percentile_baselines(populateddb_session, bmodel, bclimatology):
    sesh = populateddb_session
    if not bmodel and not bclimatology:  # no baseline! no anomaly data.
        results = percentileanomaly(
            sesh,
            default_region,
            default_climatology,
            default_variable,
            baseline_model=bmodel,
            baseline_climatology=bclimatology,
        )
        assert "anomaly" not in results
        assert "baseline" not in results
        assert "data" in results
    elif not bmodel or not bclimatology:  # badly specified baselines. error.
        with pytest.raises(werkzeug.exceptions.BadRequest):
            percentileanomaly(
                sesh,
                default_region,
                default_climatology,
                default_variable,
                baseline_model=bmodel,
                baseline_climatology=bclimatology,
            )
    elif bmodel == "fake_model" or bclimatology == "3000":  # nonexistant baselines
        with pytest.raises(werkzeug.exceptions.InternalServerError):
            percentileanomaly(
                sesh,
                default_region,
                default_climatology,
                default_variable,
                baseline_model=bmodel,
                baseline_climatology=bclimatology,
            )
    else:  # valid baseline
        assert default_response == percentileanomaly(
            sesh,
            default_region,
            default_climatology,
            default_variable,
            baseline_model=bmodel,
            baseline_climatology=bclimatology,
        )


def test_missing_models(populateddb_session):
    sesh = populateddb_session
    with pytest.raises(werkzeug.exceptions.InternalServerError):
        percentileanomaly(sesh, "missing_data", default_climatology, default_variable)


def test_extra_models(populateddb_session):
    sesh = populateddb_session
    with pytest.raises(werkzeug.exceptions.InternalServerError):
        percentileanomaly(sesh, "extra_data", default_climatology, default_variable)


@pytest.mark.parametrize("num_percentiles", [1, 2, 4, 5, 10])
def test_percentile_calculation(populateddb_session, num_percentiles):
    sesh = populateddb_session
    step = math.floor(100 / num_percentiles)
    percentiles = range(0, 100, step)
    pstring = ""
    for p in percentiles:
        pstring = pstring + "{},".format(p)
    pstring = pstring.rstrip(",")
    print(pstring)
    response = percentileanomaly(
        sesh, default_region, default_climatology, default_variable, percentile=pstring
    )
    # check that we get the right number of percentile values and that they're in the
    # right order.
    for resolution in response["anomaly"]:
        percs = resolution["values"]
        assert len(percs) == num_percentiles
        for i in range(num_percentiles - 1):
            assert percs[i] < percs[i + 1]
