#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse
import threading

import peewee


def parse_args():
    """
    Parse arguments provided at running the python program.
    """
    parser = argparse.ArgumentParser(
        description="HUME device controller"
    )

    parser.add_argument("-cdb",
                        "--clean-db",
                        action="store_true",
                        help="Clean all tables in local Postgres DB 'hume'")

    subparsers = parser.add_subparsers(help="supported commands")

    runserver_parser = subparsers.add_parser("runserver",
                                             help="Run a local HUME "
                                                  "development server.")

    runserver_parser.add_argument("hume_uuid",
                                  type=str,
                                  help="UUID for the HUME instance")
    runserver_parser.set_defaults(func=run_dev_server)

    clean_db_parser = subparsers.add_parser("clean-db",
                                            help="Clean the local DB.")
    clean_db_parser.set_defaults(func=clean_db)

    test_parser = subparsers.add_parser("test",
                                        help="Run tests.")
    test_parser.set_defaults(func=test)

    return parser.parse_args()


"""
Subparsers below
"""


def run_dev_server(runserver_args):
    """
    Runs a local development server for HUME, starting both HC and DC.

    :param runserver_args: arguments for the 'runserver' command
    """
    print("starting HUME development server...\n")

    def start_dc(args):
        optional_args = []

        base_cmd = ["python", "dc/main.py", args.hume_uuid]
        base_cmd.extend(optional_args)
        subprocess.run(base_cmd)

    def start_hc(args):
        optional_args = []

        base_cmd = ["python", "hc/main.py", args.hume_uuid]
        base_cmd.extend(optional_args)
        subprocess.run(base_cmd)

    dc_thread = threading.Thread(target=start_dc,
                                 args=(runserver_args,))
    hc_thread = threading.Thread(target=start_hc,
                                 args=(runserver_args,))
    dc_thread.start()
    hc_thread.start()
    threading.Event().wait()


def clean_db(_):
    """
    Clean the local Postgres DB 'hume' of all table content. If new tables are
    added to HUME, they must be added here as well, I don't have the energy for
    fixing automatic discovery.

    :param _: CLI args
    """
    # Fix path to solve import errors
    root_path = os.getcwd()
    subproject_dc = "dc"
    subproject_hc = "hc"

    sys.path.append(f"{root_path}/{subproject_dc}")
    sys.path.append(f"{root_path}/{subproject_hc}")

    from dc.device.models import Device
    from hc.hint.models import BrokerCredentials, HumeUser

    print("clearing the local Postgres DB 'hume' of all tables...\n")

    psql_db = peewee.PostgresqlDatabase("hume",
                                        user="hume",
                                        password="password")
    psql_db.connect()
    psql_db.drop_tables([Device, BrokerCredentials, HumeUser])

    # Remove the two added paths
    sys.path = sys.path[:-2]


def test(_):
    """
    Run all tests for HUME.
    :param _: CLI args
    """

    def prep_path_for_tests_in(path=None):
        test_path = f"{root_path}/{path}" if path else root_path
        os.chdir(test_path)
        sys.path.append(test_path)

    def run_coverage_tests(discover_args=None):
        cmd = ["coverage", "run", "-m", "unittest", "discover"]
        cmd.extend(discover_args) if discover_args else None
        proc_res = subprocess.run(cmd)
        if proc_res.returncode != 0:
            sys.exit(proc_res.returncode)

    subproject_dc = "dc"
    subproject_hc = "hc"
    root_path = os.getcwd()

    prep_path_for_tests_in(subproject_dc)
    print("Running DC unit tests")
    run_coverage_tests()

    # Remove DC path before executing HC tests
    sys.path = sys.path[:-1]

    prep_path_for_tests_in(subproject_hc)
    print("Running HC unit tests")
    run_coverage_tests()

    # Remove HC path before executing integration tests
    sys.path = sys.path[:-1]

    prep_path_for_tests_in()  # Needed to set the cwd
    print("Running integration tests")
    run_coverage_tests(discover_args=["-s", "tests"])


if __name__ == "__main__":
    cli_args = parse_args()
    if cli_args.clean_db:
        clean_db(None)

    try:
        cli_args.func(cli_args)
    except AttributeError:
        print("no command specified...")
