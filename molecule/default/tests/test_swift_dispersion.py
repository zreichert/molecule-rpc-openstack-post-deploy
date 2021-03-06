import os
import testinfra.utils.ansible_runner
import pytest
import pytest_rpc.helpers as helpers

"""ASC-296: Verify rings have data in them and that balance in the ring file
is less than 1.00.

See RPC 10+ Post-Deployment QC process document
"""

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('os-infra_hosts')[:1]


@pytest.mark.test_id('d7fc4cdc-432a-11e8-a5dc-6a00035510c0')
@pytest.mark.jira('ASC-300')
def test_verify_dispersion_populate(host):
    """Verify swift-dispersion-populate runs without error."""

    result = helpers.run_on_swift('swift-dispersion-populate --no-overlap', host)
    assert result.rc == 0


@pytest.mark.test_id('d7fc4e61-432a-11e8-bcf5-6a00035510c0')
@pytest.mark.jira('ASC-300')
def test_verify_dispersion_report(host):
    """Verify swift-dispersion-report runs without error."""

    result = helpers.run_on_swift('swift-dispersion-report', host)
    assert result.rc == 0
