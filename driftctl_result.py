"""
    Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
    SPDX-License-Identifier: MIT-0

    Permission is hereby granted, free of charge, to any person obtaining a copy of this
    software and associated documentation files (the "Software"), to deal in the Software
    without restriction, including without limitation the rights to use, copy, modify,
    merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
    permit persons to whom the Software is furnished to do so.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
    INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
    PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
    OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import json
import argparse
import subprocess
import textwrap
import os
import sys
import glob
import csv
from enum import Enum
from typing import List
from tabulate import tabulate

# Preserve white space while printing tabular view
tabulate.PRESERVE_WHITESPACE = True


class DriftctlOutputMode(Enum):
    """
    ENUM for output mode
    """
    STDOUT = 1
    FILE = 2


class DriftctlOutputFormat(Enum):
    """
    ENUM for output format
    """
    TABLE = 1
    CSV = 2


class DriftctlResourceType(Enum):
    """
    ENUM for driftctl json resource types
    """
    MANAGED = 1
    UNMANAGED = 2
    MISSING = 3
    DIFF = 4


class DriftctlResourceMin:
    """
    Drifctl object created after reading driftctl output json
    """

    def __init__(self, **kwargs):
        self.id: str = kwargs.get('id')
        self.type: str = kwargs.get('type')
        self.source: str = kwargs.get('source', "")
        self.change_log = kwargs.get('change_log')
        self.region = kwargs.get("region", "")
        self.account_id = kwargs.get("account_id", "")

    def __hash__(self):
        return hash(self.id + self.type + self.source)

    def __eq__(self, other):
        if not isinstance(other, DriftctlResourceMin):
            return False
        return self.id == other.id and self.type == other.type and (
                self.source == other.source or (self.source is None or other.source is None))


class DriftctlOutput:
    """
    Driftctl output combining all results retrieved as per command line input
    """

    def __init__(self):
        self.differences = {}
        self.managed = {}
        self.missing = {}
        self.unmanaged = {}

    def __add_resource(self, resource_type: DriftctlResourceType, resource: DriftctlResourceMin):
        """
        Check and add driftctl scan output resource to either managed, missing, unmanaged or difference cache,
        based on resource_type and append source to existing resource.

        :param resource_type: DriftctlResourceType
        :param resource: DriftctlResourceMin
        :return:
        """
        sep = ", "
        hash_key = hash(resource.id + "" + resource.type)
        if resource_type == DriftctlResourceType.UNMANAGED:
            if hash_key in self.unmanaged:
                cached_resource = self.unmanaged.get(hash_key)
                if resource.source != cached_resource.source and cached_resource.source.find(resource.source) == -1:
                    cached_resource.source = cached_resource.source + sep + resource.source
            else:
                self.unmanaged[hash_key] = resource
        elif resource_type == DriftctlResourceType.MANAGED:
            if hash_key in self.managed:
                cached_resource = self.managed.get(hash_key)
                if resource.source != cached_resource.source and cached_resource.source.find(resource.source) == -1:
                    cached_resource.source = cached_resource.source + sep + resource.source
            else:
                self.managed[hash_key] = resource
        elif resource_type == DriftctlResourceType.MISSING:
            if hash_key in self.missing:
                cached_resource = self.missing.get(hash_key)
                if resource.source != cached_resource.source and cached_resource.source.find(resource.source) == -1:
                    cached_resource.source = cached_resource.source + sep + resource.source
            else:
                self.missing[hash_key] = resource
        elif resource_type == DriftctlResourceType.DIFF:
            if hash_key in self.differences:
                cached_resource = self.differences.get(hash_key)
                if resource.source != cached_resource.source and cached_resource.source.find(resource.source) == -1:
                    cached_resource.source = cached_resource.source + sep + resource.source
            else:
                self.differences[hash_key] = resource

    def add_unmanaged_resource(self, resource: DriftctlResourceMin):
        """
        Add unmanaged resource to respective object dictionary
        :param resource: DriftctlResourceMin
        :return:
        """
        self.__add_resource(DriftctlResourceType.UNMANAGED, resource)

    def add_managed_resource(self, resource: DriftctlResourceMin):
        """
        Add managed resource to respective object dictionary
        :param resource: DriftctlResourceMin
        :return:
        """
        self.__add_resource(DriftctlResourceType.MANAGED, resource)

    def add_missing_resource(self, resource: DriftctlResourceMin):
        """
        Add missing resource to respective object dictionary
        :param resource: DriftctlResourceMin
        :return:
        """
        self.__add_resource(DriftctlResourceType.MISSING, resource)

    def add_changed_resource(self, resource: DriftctlResourceMin):
        """
        Add changed resource to respective object dictionary
        :param resource: DriftctlResourceMin
        :return:
        """
        self.__add_resource(DriftctlResourceType.DIFF, resource)

    def get_summary(self):
        """
        Get summary for Driftctl scan resource cached on this object.

        :return: DriftctlSummary
        """
        return DriftctlSummary(
            total_managed=len(self.managed),
            total_missing=len(self.missing),
            total_unmanaged=len(self.unmanaged),
            total_changed=len(self.differences)
        )

    def __eq__(self, other):
        if not isinstance(other, DriftctlOutput):
            return False
        return self.differences == other.differences and self.missing == other.missing \
               and self.unmanaged == other.unmanaged and self.managed == other.managed


class DriftctlSummary:
    """
    Class for holding state for Driftctl scanned resources summary.
    """

    def __init__(self, **kwargs):
        self.total_changed = kwargs.get('total_changed', 0)
        self.total_unmanaged = kwargs.get('total_unmanaged', 0)
        self.total_missing = kwargs.get('total_missing', 0)
        self.total_managed = kwargs.get('total_managed', 0)
        self.total_resources = self.total_managed + self.total_unmanaged + self.total_missing
        self.coverage = int(self.total_managed * 100 / self.total_resources) if self.total_resources > 0 else 0

    def get_total_resources_count(self):
        """
        Get count of total changed resources
        :return:
        """
        return self.total_resources

    def get_coverage_stats(self):
        """
        Get coverage statistics for driftctl run
        :return:
        """
        return self.coverage

    def __eq__(self, other):
        if not isinstance(other, DriftctlSummary):
            return False
        return self.total_changed == other.total_changed and self.total_managed == other.total_managed and \
               self.coverage == other.coverage and self.total_resources == other.total_resources and \
               self.total_missing == other.total_missing and self.total_unmanaged == other.total_unmanaged


def get_driftctl_resource(resource: dict, region: str = "", account_id: str = "", source_file_name: str = "",
                          wrap_text: bool = False):
    """

    Get DriftctlResourceMin object with details provided.

    :param resource: Resource dictionary retrieved from Driftctl scan output json file.
    :param region: Cloud provider region name from where resource details are being retrieved.
    :param account_id: Cloud provider account_id or analogical details from where resource details are being retrieved.
    :param source_file_name: Driftctl scan output json file name from where the details are being retrieved.
    :param wrap_text: if True, values for id and type key from resource dict are being wrapped with column size of 30
    :return: DriftctlResourceMin

    """
    _id = resource.get('id', "") if not wrap_text else "\n".join(textwrap.wrap(resource.get('id', "")))
    _type = resource.get('type', "") if not wrap_text else "\n".join(textwrap.wrap(resource.get('type', "")))
    _change_log = resource.get('change_log', "")
    return DriftctlResourceMin(id=_id, type=_type, source=source_file_name, change_log=_change_log,
                               region=region, account_id=account_id)


def get_driftctl_combined_output(driftctl_output_json_dicts=None, wrap_text: bool = False):
    """

    Analyse and merge, all Driftctl scan output json files dict(s) and produce a combined output.

    :param driftctl_output_json_dicts: List of Drifctl scan output json dict.
    :param wrap_text: if True, details for resource under driftctl_output_json_dicts are wrapped to be displayed.
    :return: DriftctlOutput
    """
    if driftctl_output_json_dicts is None:
        driftctl_output_json_dicts = []
    driftctl_output = DriftctlOutput()
    for drift_output in driftctl_output_json_dicts:
        source_file_name = drift_output.get('source_file_name')
        region = drift_output.get('resource_region')
        account_id = drift_output.get('resource_account_id')

        if drift_output.get('unmanaged') is not None:
            for unmanaged_resource in drift_output.get('unmanaged'):
                driftctl_output.add_unmanaged_resource(
                    get_driftctl_resource(unmanaged_resource, region, account_id, source_file_name, wrap_text))
        if drift_output.get('missing') is not None:
            for missing_resource in drift_output.get('missing'):
                driftctl_output.add_missing_resource(
                    get_driftctl_resource(missing_resource, region, account_id, source_file_name, wrap_text))

        if drift_output.get('differences') is not None:
            for difference in drift_output.get('differences'):
                res = difference.get('res')
                res["change_log"] = difference.get('changelog')
                driftctl_output.add_changed_resource(get_driftctl_resource(res, region, account_id,
                                                                           source_file_name, wrap_text))
        if drift_output.get('managed') is not None:
            for managed_resource in drift_output.get('managed'):
                driftctl_output.add_managed_resource(
                    get_driftctl_resource(managed_resource, region, account_id, source_file_name, wrap_text))
    return driftctl_output


def print_data_table(writer, data=None, headers=None):
    """
    Print table on screen with tabulate, with fancy_grid format, for provided data and headers.
    :param writer: IO Handler for writing output.
    :param data: List of list of data to be added to table.
    :param headers: Headers for the table
    """
    if headers is None:
        headers = ["No Data"]
    if data is None:
        data = [["No Data"]]
    print(tabulate(data, headers=headers, tablefmt="fancy_grid", colalign=("right",)), file=writer)
    writer.flush()


def print_data_csv(writer, data=None, headers=None):
    """
    Print data on screen in CSV format, along with headers.
    :param writer: IO Handler for writing output.
    :param data:List of list of data to be added to table.
    :param headers: Headers for the csv file

    """
    if headers is None:
        headers = []
    if data is None:
        data = []
    csv_writer = csv.writer(writer)
    csv_writer.writerow(headers)
    csv_writer.writerows(data)


def print_driftctl_op(output: DriftctlOutput, print_details: bool = False,
                      output_file_mode: DriftctlOutputMode = DriftctlOutputMode.STDOUT,
                      output_file_name: str = "",
                      output_file_format: DriftctlOutputFormat = DriftctlOutputFormat.TABLE):
    """
    Print details of output in tabular or csv format on provided file mode.

    :param output: Driftctl output object.
    :param print_details: If True, print details TABLE or CSV after printing Summary details.
    :param output_file_mode: DriftctlOutputMode, defaults to STDOUT
    :param output_file_name: if output_file_mode is not STDOUT, then output will be written to the file name provided.
    if output_file_mode is CSV, then output_file_name should end with csv, else .csv will be appended to the
    provided output file name.
    :param output_file_format: DriftctlOutputFormat, defaults to TABLE.

    """
    # Generate table for summary
    summary_table = []
    summary_headers = ["Summary", "count"]
    summary = output.get_summary()
    summary_table.append(["Coverage", f"{summary.coverage}%"])
    summary_table.append(["Found resource(s)", summary.total_resources])
    summary_table.append(["Resource(s) managed by Terraform", summary.total_managed])
    summary_table.append(["Resource(s) found in a Terraform state but missing on the cloud provider",
                          summary.total_missing])
    summary_table.append(["Resource(s) not managed by Terraform", summary.total_unmanaged])
    summary_table.append(["Resource(s) out of sync with Terraform state", summary.total_changed])

    writer = sys.stdout
    try:
        if output_file_mode == DriftctlOutputMode.FILE:
            if output_file_format == DriftctlOutputFormat.CSV:
                if not output_file_name.lower().endswith(".csv"):
                    output_file_name = f"{output_file_name}.csv"
                writer = open(output_file_name, "w", encoding="utf-8")
            elif output_file_format == DriftctlOutputFormat.TABLE:
                writer = open(output_file_name, "w", encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: Cannot open file {output_file_name} to write data", file=sys.stderr)
        print("Warn: Output will be written to STDOUT instead", file=sys.stderr)
    if output_file_format == DriftctlOutputFormat.TABLE:
        print_data_table(writer=writer, data=summary_table, headers=summary_headers)
    elif output_file_format == DriftctlOutputFormat.CSV:
        print_data_csv(writer=writer, data=summary_table, headers=summary_headers)

    # Print detail view if there are resources missing coverage.
    if summary.coverage < 100 and print_details:
        # Added/Print separator between summary and detail view.
        print(
            "\n--------------------------------------------------------------------------------------------------------"
            "-------------------------------------------------------------------\n", file=writer)
        detail_headers = ["Category", "Resource Id", "Resource Type", "Region", "Account Id", "Source"]
        detail_table = []
        for missing in output.missing.values():
            _id = missing.id
            _source = missing.source
            if output_file_format == DriftctlOutputFormat.TABLE:
                _id = "\n".join(textwrap.wrap(_id))
                _source = "\n".join(textwrap.wrap(_source, width=40))
            detail_table.append(["Missing", _id, missing.type, missing.region, missing.account_id, _source])

        for unmanaged in output.unmanaged.values():
            _id = unmanaged.id
            _source = unmanaged.source
            if output_file_format == DriftctlOutputFormat.TABLE:
                _id = "\n".join(textwrap.wrap(_id))
                _source = "\n".join(textwrap.wrap(_source, width=40))
            detail_table.append(["Unmanaged", _id, unmanaged.type, unmanaged.region, unmanaged.account_id, _source])
        for diff in output.differences.values():
            _id = diff.id
            _source = diff.source
            if output_file_format == DriftctlOutputFormat.TABLE:
                _id = "\n".join(textwrap.wrap(_id))
                _source = "\n".join(textwrap.wrap(_source, width=40))
            detail_table.append(["Changed", _id, diff.type, diff.region, diff.account_id, _source])

        if output_file_format == DriftctlOutputFormat.TABLE:
            print_data_table(writer=writer, data=detail_table, headers=detail_headers)
        elif output_file_format == DriftctlOutputFormat.CSV:
            print_data_csv(writer=writer, data=detail_table, headers=detail_headers)
    writer.close()


def parse_arguments(_args):
    """
    Parse commandline arguments
    :param _args:
    :return:
    """
    parser = argparse.ArgumentParser(description="Scan driftctl scan json output and combine results.")
    parser.add_argument("-i", "--input-dir", type=str, dest="root_dir",
                        default=os.path.dirname(os.path.abspath(__file__)))
    parser.add_argument("-f", "--file-name", type=str, dest="file_name", default="driftctl-result.json")
    parser.add_argument("--detailed", dest="detailed", default=False, action='store_true')
    parser.add_argument("--output", "-o", dest="output_file", default="STDOUT")
    parser.add_argument("--output-format", "-p", dest="output_format", choices=["TABLE", "CSV"], default="TABLE")
    return parser.parse_args(_args)


def find_files(root_dir, file_name):
    """
    Find file_name from root_dir using glob
    :param root_dir: root directory name from which to find the files.
    :param file_name: file name to searched from the root directory.
    :return: list of files
    """
    return glob.glob(root_dir + os.sep + "**" + os.sep + file_name, recursive=True)


def get_terraform_output(dir_name: str):
    """

    Run terraform output command in the directory name provided and return dict of the output.
    In case of error while getting output empty dict is returned.

    :param dir_name: Name/Path of the directory consisting of Initialized terraform configuration.
    :return: dict

    """
    try:
        output = subprocess.check_output("terraform -chdir=\"" + dir_name + "\" output -json", shell=True)
        return json.loads(output)
    except Exception:
        print(f"WARN : Not able to get details from terraform output for directory {dir_name}", file=sys.stderr)
        return {}


def get_account_details_from_terraform_output(dir_name: str):
    """

    Get region and account id details using terraform cli, using output values "resource_region"
    and "resource_account_id", if details are not found for either, empty string is returned.

    :param dir_name: directory where terraform configuration exists to get terraform output.
    :return: resource_region(str), resource_account_id (str)
    """
    tf_output = get_terraform_output(dir_name=dir_name)
    resource_region = tf_output.get("resource_region", {}).get("value", "")
    resource_account_id = tf_output.get("resource_account_id", {}).get("value", "")
    return str(resource_region), str(resource_account_id)


def validate_and_load_driftctl_scan_json(files: List[str]):
    """

    Reads list of Driftctl scan output json files, converts it to dict, and add details of
    source_file_name, resource_region and resource_account_id to each file, and return list of Driftctl scan output
    json dict.

    :param files: List of Driftctl scan output json files
    :return: List of dict

    """
    drift_scan_dicts = []
    for in_file in files:
        try:
            resource_region, resource_account_id = get_account_details_from_terraform_output(os.path.dirname(in_file))
            with open(in_file, "r", encoding="utf-8") as infile:
                _my_dict = json.load(infile)
                file_name = "." + in_file[len(os.getcwd()):] if in_file.find(os.getcwd()) == 0 else in_file
                _my_dict["source_file_name"] = file_name
                _my_dict["resource_region"] = resource_region
                _my_dict["resource_account_id"] = resource_account_id
                drift_scan_dicts.append(_my_dict)
                infile.close()
        except Exception:
            print(f"Warning : Not able to read driftctl scan output json file {in_file}, "
                  f"data for this file will be ignored.", file=sys.stderr)
    return drift_scan_dicts


if __name__ == '__main__':
    args = parse_arguments(sys.argv[1:])
    op_format: DriftctlOutputFormat = DriftctlOutputFormat.CSV if args.output_format == "CSV" \
        else DriftctlOutputFormat.TABLE
    print_driftctl_op(
        output=get_driftctl_combined_output(
            driftctl_output_json_dicts=validate_and_load_driftctl_scan_json(find_files(args.root_dir, args.file_name)),
        ),
        print_details=args.detailed,
        output_file_format=op_format,
        output_file_mode=DriftctlOutputMode.STDOUT if args.output_file == "STDOUT" else DriftctlOutputMode.FILE,
        output_file_name=args.output_file
    )
