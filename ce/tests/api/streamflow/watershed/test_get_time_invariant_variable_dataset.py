import pytest
from sqlalchemy.orm.exc import NoResultFound
from ce.api.streamflow.watershed import get_time_invariant_variable_dataset


# TODO: Add more tests


@pytest.mark.parametrize('variable, exception', (
        ('bargle', NoResultFound),  # does not exist
        # TODO: Give tasmin-related test DataFiles a defined TimeSet and
        #  test this case.
        # ('tasmin', NoResultFound),  # exists, not time-invariant
        ('flow_direction', None),   # exists, time-invariant
))
def test_validation(populateddb, variable, exception):
    if exception:
        with pytest.raises(exception):
            file = get_time_invariant_variable_dataset(
                populateddb.session, 'ce', variable)
    else:
        file = get_time_invariant_variable_dataset(
            populateddb.session, 'ce', variable)


