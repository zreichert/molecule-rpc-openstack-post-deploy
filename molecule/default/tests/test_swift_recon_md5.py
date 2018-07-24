import os
import testinfra.utils.ansible_runner
import pytest

"""ASC-298: Verify md5 sums of ring files using swift-recon tool

See RPC 10+ Post-Deployment QC process document
"""

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('os-infra_hosts')[:1]


# Helpers
def run_on_container(command, container, run_on_host):
    """Run the given command on the given container.

    Args:
        command (str): The bash command to run.
        container (str): The container type to run the command on.
        run_on_host (testinfra.Host): Testinfra host object to execute the
                                      wrapped command on.

    Returns:
        testinfra.CommandResult: Result of command execution.
    """

    pre_command = "lxc-attach \
                   -n $(lxc-ls -1 | grep {} | head -n 1) \
                   -- bash -c ".format(container)
    cmd = "{} '{}'".format(pre_command, command)
    return run_on_host.run(cmd)


def run_on_swift(cmd, run_on_host):
    """Run the given command on the swift container.
    Args:
        cmd (str): Command
        run_on_host (testinfra.Host): Testinfra host object to execute the
                                      wrapped command on.
    Returns:
        testinfra.CommandResult: Result of command execution.
    """

    command = (". ~/openrc ; "
               ". /openstack/venvs/swift-*/bin/activate ; "
               "{}".format(cmd))
    return run_on_container(command, 'swift', run_on_host)


def parse_swift_recon(recon_out):
    """Parse swift-recon output into list of lists grouped by the content of
    the delimited blocks.

    Args:
        recon_out (str): CLI output from the `swift-recon` command.

    Returns:
        list: List of lists grouped by the content of the delimited blocks

    Example output from `swift-recon --md5` to be parsed:
    ===============================================================================
    --> Starting reconnaissance on 3 hosts (object)
    ===============================================================================
    [2018-07-19 15:36:40] Checking ring md5sums
    3/3 hosts matched, 0 error[s] while checking hosts.
    ===============================================================================
    [2018-07-19 15:36:40] Checking swift.conf md5sum
    3/3 hosts matched, 0 error[s] while checking hosts.
    ===============================================================================
    """

    lines = recon_out.splitlines()
    collection = []
    data = []
    inData = False
    i = 0
    while i < len(lines):
        if not inData:
            if lines[i].startswith('=' * 79):
                inData = True
        elif lines[i].startswith('=' * 79):
            inData = False
            collection.append(data)
            data = []
            # Reset counter to use the delimeter to trigger data collection in
            # the next pass.
            i = i - 1
        else:
            data.append(lines[i])
        i = i + 1
    return collection


@pytest.mark.test_id('d7fc49a8-432a-11e8-a2ea-6a00035510c0')
@pytest.mark.jira('ASC-298')
def test_verify_swift_ring_md5sums(host):
    """Verify the swift ring md5sums with local copy using swift-recon.

    """

    swift_md5_out = run_on_swift('swift-recon --md5', host).stdout
    swift_data = parse_swift_recon(swift_md5_out)

    assert len(swift_data) > 2, "swift-recon did not return expected data"

    starting_line = swift_data[0][0]
    swift_count = next(iter([int(s) for s in starting_line.split() if
                             s.isdigit()]), None)

    # assert no errors found and that all hosts were matched
    for element in swift_data[1:]:
        assert '0 error' in element[-1], ('Errors found in {}'
                                          .format(element[0]))
        assert "{}/{} hosts matched".format(swift_count,
                                            swift_count) in element[-1], \
               "Not all hosts matched in {}" .format(element[0])
