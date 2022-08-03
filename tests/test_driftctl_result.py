"""
Test cases for Driftctl result python script that merges drifctl output data from multiple folders and combines results
"""
import unittest
import sys
import os
import tempfile

from driftctl_result import DriftctlSummary, get_driftctl_resource, DriftctlResourceMin, DriftctlOutput, \
    get_terraform_output, find_files, get_driftctl_combined_output, validate_and_load_driftctl_scan_json, \
    print_data_table, print_data_csv, print_driftctl_op, DriftctlOutputMode, DriftctlOutputFormat

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + os.sep + ".." + os.sep)


def get_driftctl_op_test_objects():
    """
    Return static DriftctlResourceMin Objects pertaining to type of resrouce
    cr = Changed Resource
    mr = Managed Resource
    umr = Unmanaged Resource
    mir = Missing Resource
    :return:
    """
    return {
        'cr': DriftctlResourceMin(
            source="test-changed-source",
            account_id="test-changed-account-id",
            region="test-region",
            type="test-changed-type",
            id="test-changed-id"
        ),
        'mr': DriftctlResourceMin(
            source="test-managed-source",
            account_id="test-managed-account-id",
            region="test-managed-region",
            type="test-managed-type",
            id="test-managed-id"
        ),
        'umr': DriftctlResourceMin(
            source="test-unmanaged-source",
            account_id="test-unmanaged-account-id",
            region="test-unmanaged-region",
            type="test-unmanaged-type",
            id="test-unmanaged-id"
        ),
        'mir': DriftctlResourceMin(
            source="test-missing-source",
            account_id="test-missing-account-id",
            region="test-missing-region",
            type="test-missing-type",
            id="test-missing-id"
        ),
        'cr1': DriftctlResourceMin(
            source="test-changed-source-1",
            account_id="test-changed-account-id",
            region="test-region",
            type="test-changed-type",
            id="test-changed-id"
        ),
        'mr1': DriftctlResourceMin(
            source="test-managed-source-1",
            account_id="test-managed-account-id",
            region="test-managed-region",
            type="test-managed-type",
            id="test-managed-id"
        ),
        'umr1': DriftctlResourceMin(
            source="test-unmanaged-source-1",
            account_id="test-unmanaged-account-id",
            region="test-unmanaged-region",
            type="test-unmanaged-type",
            id="test-unmanaged-id"
        ),
        'mir1': DriftctlResourceMin(
            source="test-missing-source-1",
            account_id="test-missing-account-id",
            region="test-missing-region",
            type="test-missing-type",
            id="test-missing-id"
        )
    }


class TestDriftctlResult(unittest.TestCase):
    """
    Test cases for Driftctl Result script
    """

    def test_driftctl_summary(self):
        """
        Test Driftctl summary Class and its methods
        :return:
        """
        event = {
            "total_resources": 73,
            "total_changed": 0,
            "total_unmanaged": 71,
            "total_missing": 2,
            "total_managed": 0,
            "total_iac_source_count": 1
        }
        summary = DriftctlSummary(**event)
        self.assertEqual(summary.get_total_resources_count(), 73)
        self.assertEqual(summary.get_coverage_stats(), 0)

        summary = DriftctlSummary()
        self.assertEqual(summary.get_total_resources_count(), 0)
        self.assertEqual(summary.get_coverage_stats(), 0)

        event = {
            "total_resources": 73,
            "total_changed": 0,
            "total_unmanaged": 71,
            "total_missing": 0,
            "total_managed": 2,
            "total_iac_source_count": 1
        }
        summary = DriftctlSummary(**event)
        self.assertEqual(summary.get_total_resources_count(), 73)
        self.assertEqual(summary.get_coverage_stats(), int(2 * 100 / 73))

    def test_get_driftctl_resource(self):
        """
        Test get_driftctl_resource function
        :return:
        """
        test_id = "i-09039f97729659bd6"
        test_type = "aws_instance"
        test_account_id = ""
        test_region = ""
        test_source_file_name = ""
        resource = {
            "id": test_id,
            "type": test_type,
            "human_readable_attributes": {
                "Name": "driftctl-acc-a-use1"
            },
            "source": {
                "source": "terraform.tfstate",
                "namespace": "module.ec2",
                "internal_name": "instance"
            }
        }
        resource_observe = DriftctlResourceMin(id=test_id, type=test_type, account_id=test_account_id,
                                               region=test_region, source=test_source_file_name)
        self.assertEqual(get_driftctl_resource(resource=resource, region=test_region, account_id=test_account_id,
                                               source_file_name=test_source_file_name), resource_observe)

    def test_driftctl_output(self):
        """
        Test Driftctl Output class and its methods
        :return:
        """
        driftctl_op_test_objects = get_driftctl_op_test_objects()
        driftctl_output = DriftctlOutput()
        self.assertNotEqual(driftctl_output, DriftctlOutput)
        driftctl_output.add_changed_resource(resource=driftctl_op_test_objects.get('cr'))
        self.assertEqual(driftctl_output.get_summary(), DriftctlSummary(total_changed=1))
        driftctl_output.add_managed_resource(resource=driftctl_op_test_objects.get('mr'))
        self.assertEqual(driftctl_output.get_summary(), DriftctlSummary(total_changed=1, total_managed=1))
        driftctl_output.add_unmanaged_resource(resource=driftctl_op_test_objects.get('umr'))
        self.assertEqual(driftctl_output.get_summary(), DriftctlSummary(total_changed=1, total_managed=1,
                                                                        total_unmanaged=1))
        driftctl_output.add_missing_resource(resource=driftctl_op_test_objects.get('mir'))
        self.assertEqual(driftctl_output.get_summary(), DriftctlSummary(total_changed=1, total_managed=1,
                                                                        total_unmanaged=1, total_missing=1))
        # Adding resource with different source should not increase number of resource, else source should be appended.
        driftctl_output.add_changed_resource(resource=driftctl_op_test_objects.get('cr1'))
        self.assertEqual(driftctl_output.get_summary(), DriftctlSummary(total_changed=1, total_managed=1,
                                                                        total_unmanaged=1, total_missing=1))
        driftctl_output.add_managed_resource(resource=driftctl_op_test_objects.get('mr1'))
        self.assertEqual(driftctl_output.get_summary(), DriftctlSummary(total_changed=1, total_managed=1,
                                                                        total_unmanaged=1, total_missing=1))
        driftctl_output.add_unmanaged_resource(resource=driftctl_op_test_objects.get('umr1'))
        self.assertEqual(driftctl_output.get_summary(), DriftctlSummary(total_changed=1, total_managed=1,
                                                                        total_unmanaged=1, total_missing=1))
        driftctl_output.add_missing_resource(resource=driftctl_op_test_objects.get('mir1'))
        self.assertEqual(driftctl_output.get_summary(), DriftctlSummary(total_changed=1, total_managed=1,
                                                                        total_unmanaged=1, total_missing=1))

    def test_get_terraform_output(self):
        """
        Test get terraform output from drirectory where driftctlfile is present
        for this test there is no terraform state so only exception scenario will be tested.
        :return:
        """
        temp_dir = tempfile.gettempdir()
        self.assertEqual(get_terraform_output(temp_dir), {})

    def test_get_terraform_output_sub_process_inject(self):
        """
        Test get terraform output from drirectory where driftctlfile is present
        for this test there is no terraform state so only exception scenario will be tested.
        :return:
        """
        temp_dir = tempfile.gettempdir()
        injection_dir_name = "injected_dir"

        injection_1 = "\";mkdir "+temp_dir+os.sep+injection_dir_name+";\""
        get_terraform_output(injection_1)
        self.assertFalse(os.path.exists(temp_dir+os.sep+injection_dir_name))

        injection_2 = "\\\";mkdir "+temp_dir+os.sep+injection_dir_name+";\\\""
        get_terraform_output(injection_2)
        self.assertFalse(os.path.exists(temp_dir+os.sep+injection_dir_name))

        injection_3 = "\\';mkdir "+temp_dir+os.sep+injection_dir_name+";\\'"
        get_terraform_output(injection_3)
        self.assertFalse(os.path.exists(temp_dir+os.sep+injection_dir_name))

        injection_4 = "\\\';mkdir "+temp_dir+os.sep+injection_dir_name+";\\\'"
        get_terraform_output(injection_4)
        self.assertFalse(os.path.exists(temp_dir+os.sep+injection_dir_name))

        injection_5 = "';mkdir "+temp_dir+os.sep+injection_dir_name+";'"
        get_terraform_output(injection_5)
        self.assertFalse(os.path.exists(temp_dir+os.sep+injection_dir_name))

        injection_6 = "\"&& mkdir "+temp_dir+os.sep+injection_dir_name+"&&\""
        get_terraform_output(injection_6)
        self.assertFalse(os.path.exists(temp_dir+os.sep+injection_dir_name))

    def test_find_files(self):
        """
        Test
        :return:
        """
        test_driftctl_json_folder = os.path.dirname(os.path.abspath(__file__)) + os.sep + "test_json"
        expected_output_files = [
            test_driftctl_json_folder + os.sep + "1" + os.sep + "test-driftctl-result.json",
            test_driftctl_json_folder + os.sep + "2" + os.sep + "test-driftctl-result.json",
            test_driftctl_json_folder + os.sep + "3" + os.sep + "test-driftctl-result.json",
            test_driftctl_json_folder + os.sep + "4" + os.sep + "test-driftctl-result.json",
        ]
        for expected_output_file in expected_output_files:
            self.assertTrue(expected_output_file in find_files(test_driftctl_json_folder, "test-driftctl-result.json"))

    def test_validate_and_load_driftctl_scan_json(self):
        """
        Test if json files are being read correctly and parsed properly.
        :return:
        """
        test_driftctl_json_folder = os.path.dirname(os.path.abspath(__file__)) + os.sep + "test_json"
        file_list = [
            test_driftctl_json_folder + os.sep + "1" + os.sep + "test-driftctl-result.json",
            test_driftctl_json_folder + os.sep + "2" + os.sep + "test-driftctl-result.json",
            test_driftctl_json_folder + os.sep + "4" + os.sep + "test-driftctl-result.json"
        ]
        self.assertEqual(len(validate_and_load_driftctl_scan_json(files=[])), 0)
        test_outputs = validate_and_load_driftctl_scan_json(files=file_list)
        self.assertEqual(len(test_outputs), 2)
        count = 1
        for test_output in test_outputs:
            self.assertTrue('source_file_name' in test_output)
            self.assertTrue('resource_region' in test_output)
            self.assertTrue('resource_account_id' in test_output)
            self.assertEqual(test_output["resource_region"], "")
            self.assertEqual(test_output["resource_account_id"], "")
            count += 1

    def test_get_driftctl_combined_output(self):
        """
        Test get driftctl combined output method using json files provided under test_json folder.
        :return:
        """
        test_output_1 = get_driftctl_combined_output()
        self.assertEqual(test_output_1, DriftctlOutput())
        self.assertEqual(test_output_1.get_summary(), DriftctlSummary())
        test_driftctl_json_folder = os.path.dirname(os.path.abspath(__file__)) + os.sep + "test_json"
        file_list = [
            test_driftctl_json_folder + os.sep + "1" + os.sep + "test-driftctl-result.json",
            test_driftctl_json_folder + os.sep + "2" + os.sep + "test-driftctl-result.json"
        ]
        test_output = get_driftctl_combined_output(
            driftctl_output_json_dicts=validate_and_load_driftctl_scan_json(file_list)
        )
        # Unmanaged policies are common in both files
        # 2 managed - file 1
        # 2 managed - file 2
        # 2 unmanaged - both files
        self.assertEqual(test_output.get_summary().get_total_resources_count(), 6)

    def test_print_data_table(self):
        """
        Test print data table function that prints output in tabular format. and No data output if no data is provided.
        :return:
        """
        # print file
        file_name = "./test_file.txt"
        with open(file_name, "a", encoding="utf-8") as test_file:
            try:
                print_data_table(writer=test_file, headers=["Data", "Count"], data=[["a", "1"], ["b", "2"]])
                temp_file_name = test_file.name
                with open(temp_file_name, "r", encoding="utf-8") as content:
                    data = content.read()
                    self.assertEqual(data, "╒════════╤═════════╕\n│   Data │   Count │\n╞════════╪═════════╡\n│      "
                                           "a │       1 │\n├────────┼─────────┤\n│      b │       2 "
                                           "│\n╘════════╧═════════╛\n")
                test_file.close()
            finally:
                os.unlink(file_name)
        with open(file_name, "a", encoding="utf-8") as test_file_1:
            try:
                print_data_table(test_file_1)
                with open(test_file_1.name, "r", encoding="utf-8") as content:
                    data = content.read()
                    expected_output = "╒═══════════╕\n" \
                                      "│   No Data │\n" \
                                      "╞═══════════╡\n" \
                                      "│   No Data │\n" \
                                      "╘═══════════╛\n"
                    self.assertEqual(data, expected_output)
                test_file_1.close()
            finally:
                os.unlink(file_name)

    def test_print_data_csv(self):
        """
        Test print data csv method, responsible to write data to csv file, on file handler provided as input.
        :return:
        """
        file_name_csv = "test_file.csv"
        with open(file_name_csv, "a", encoding="utf-8") as test_file_csv:
            print_data_csv(writer=test_file_csv, headers=["Data", "Count"], data=[["a", "1"], ["b", "2"]])
            test_file_csv.close()
        with open(file_name_csv, "r", encoding="utf-8") as content:
            data = content.read()
            self.assertEqual(data, "Data,Count\na,1\nb,2\n")
        os.unlink(file_name_csv)

    def test_print_driftctl_op(self):
        """
        Test print driftctl output function responsible for writing output either to sysout or to file
        as per inputs provided by user.
        :return:
        """
        driftctl_op = DriftctlOutput()
        driftctl_op_test_objects = get_driftctl_op_test_objects()
        driftctl_op.add_changed_resource(resource=driftctl_op_test_objects.get('cr'))
        driftctl_op.add_managed_resource(resource=driftctl_op_test_objects.get('mr'))
        driftctl_op.add_unmanaged_resource(resource=driftctl_op_test_objects.get('umr'))
        driftctl_op.add_missing_resource(resource=driftctl_op_test_objects.get('mir'))
        expected_op_tb = "╒══════════════════════════════════════════════════════════════════════════╤═════════╕\n" \
                         "│                                                                  Summary │ count   │\n" \
                         "╞══════════════════════════════════════════════════════════════════════════╪═════════╡\n" \
                         "│                                                                 Coverage │ 33%     │\n" \
                         "├──────────────────────────────────────────────────────────────────────────┼─────────┤\n" \
                         "│                                                        Found resource(s) │ 3       │\n" \
                         "├──────────────────────────────────────────────────────────────────────────┼─────────┤\n" \
                         "│                                         Resource(s) managed by Terraform │ 1       │\n" \
                         "├──────────────────────────────────────────────────────────────────────────┼─────────┤\n" \
                         "│ Resource(s) found in a Terraform state but missing on the cloud provider │ 1       │\n" \
                         "├──────────────────────────────────────────────────────────────────────────┼─────────┤\n" \
                         "│                                     Resource(s) not managed by Terraform │ 1       │\n" \
                         "├──────────────────────────────────────────────────────────────────────────┼─────────┤\n" \
                         "│                             Resource(s) out of sync with Terraform state │ 1       │\n" \
                         "╘══════════════════════════════════════════════════════════════════════════╧═════════╛\n"
        expected_op_csv = "Summary,count\nCoverage,33%\nFound resource(s),3\nResource(s) managed by Terraform,1\n" \
                          "Resource(s) found in a Terraform state but missing on the cloud provider,1\n" \
                          "Resource(s) not managed by Terraform,1\nResource(s) out of sync with Terraform state,1\n"
        op_file_name = "test_op.txt"
        print_driftctl_op(output=driftctl_op, output_file_mode=DriftctlOutputMode.FILE,
                          output_file_name=op_file_name)
        with open(op_file_name, "r", encoding="utf-8") as data_file:
            data = data_file.read()
            self.assertEqual(data, expected_op_tb)
        os.unlink(op_file_name)
        op_file_name_csv = op_file_name + ".csv"
        print_driftctl_op(output=driftctl_op, output_file_mode=DriftctlOutputMode.FILE,
                          output_file_name=op_file_name, output_file_format=DriftctlOutputFormat.CSV)
        with open(op_file_name_csv, "r", encoding="utf-8") as data_file:
            data = data_file.read()
            self.assertEqual(data, expected_op_csv)
        os.unlink(op_file_name_csv)

        driftctl_op.add_unmanaged_resource(resource=driftctl_op_test_objects.get('umr1'))

        expected_op_td = "╒══════════════════════════════════════════════════════════════════════════╤═════════╕\n" \
                         "│                                                                  Summary │ count   │\n" \
                         "╞══════════════════════════════════════════════════════════════════════════╪═════════╡\n" \
                         "│                                                                 Coverage │ 33%     │\n" \
                         "├──────────────────────────────────────────────────────────────────────────┼─────────┤\n" \
                         "│                                                        Found resource(s) │ 3       │\n" \
                         "├──────────────────────────────────────────────────────────────────────────┼─────────┤\n" \
                         "│                                         Resource(s) managed by Terraform │ 1       │\n" \
                         "├──────────────────────────────────────────────────────────────────────────┼─────────┤\n" \
                         "│ Resource(s) found in a Terraform state but missing on the cloud provider │ 1       │\n" \
                         "├──────────────────────────────────────────────────────────────────────────┼─────────┤\n" \
                         "│                                     Resource(s) not managed by Terraform │ 1       │\n" \
                         "├──────────────────────────────────────────────────────────────────────────┼─────────┤\n" \
                         "│                             Resource(s) out of sync with Terraform state │ 1       │\n" \
                         "╘══════════════════════════════════════════════════════════════════════════╧═════════╛\n\n" \
                         "-------------------------------------------------------------------------------------" \
                         "--------------------------------------------------------------------------------------\n\n" \
                         "╒════════════╤═══════════════════╤═════════════════════╤═══════════════════════" \
                         "╤═══════════════════════════╤════════════════════════════════════════╕\n" \
                         "│   Category │ Resource Id       │ Resource Type       │ Region                " \
                         "│ Account Id                │ Source                                 │\n" \
                         "╞════════════╪═══════════════════╪═════════════════════╪═══════════════════════" \
                         "╪═══════════════════════════╪════════════════════════════════════════╡\n" \
                         "│    Missing │ test-missing-id   │ test-missing-type   │ test-missing-region   " \
                         "│ test-missing-account-id   │ test-missing-source                    │\n" \
                         "├────────────┼───────────────────┼─────────────────────┼───────────────────────" \
                         "┼───────────────────────────┼────────────────────────────────────────┤\n" \
                         "│  Unmanaged │ test-unmanaged-id │ test-unmanaged-type │ test-unmanaged-region " \
                         "│ test-unmanaged-account-id │ test-unmanaged-source, test-unmanaged- │\n" \
                         "│            │                   │                     │                       " \
                         "│                           │ source-1                               │\n" \
                         "├────────────┼───────────────────┼─────────────────────┼───────────────────────" \
                         "┼───────────────────────────┼────────────────────────────────────────┤\n" \
                         "│    Changed │ test-changed-id   │ test-changed-type   │ test-region           " \
                         "│ test-changed-account-id   │ test-changed-source                    │\n" \
                         "╘════════════╧═══════════════════╧═════════════════════╧═══════════════════════" \
                         "╧═══════════════════════════╧════════════════════════════════════════╛\n"

        expected_op_csvd = "Summary,count\nCoverage,33%\nFound resource(s),3\nResource(s) managed by Terraform,1\n" \
                           "Resource(s) found in a Terraform state but missing on the cloud provider,1\n" \
                           "Resource(s) not managed by Terraform,1\nResource(s) out of sync with Terraform state,1\n\n"\
                           "---------------------------------------------------------------------------------------" \
                           "------------------------------------------------------------------------------------\n\n" \
                           "Category,Resource Id,Resource Type,Region,Account Id,Source\n" \
                           "Missing,test-missing-id,test-missing-type,test-missing-region" \
                           ",test-missing-account-id,test-missing-source\n" \
                           "Unmanaged,test-unmanaged-id,test-unmanaged-type,test-unmanaged-region" \
                           ",test-unmanaged-account-id,\"test-unmanaged-source, test-unmanaged-source-1\"\n" \
                           "Changed,test-changed-id,test-changed-type,test-region," \
                           "test-changed-account-id,test-changed-source\n"

        print_driftctl_op(output=driftctl_op, output_file_mode=DriftctlOutputMode.FILE,
                          output_file_name=op_file_name, print_details=True)
        with open(op_file_name, "r", encoding="utf-8") as data_file_op:
            data_op = data_file_op.read()
            os.unlink(op_file_name)
            self.assertEqual(data_op, expected_op_td)

        print_driftctl_op(output=driftctl_op, output_file_mode=DriftctlOutputMode.FILE,
                          output_file_name=op_file_name_csv, print_details=True,
                          output_file_format=DriftctlOutputFormat.CSV)
        with open(op_file_name_csv, "r", encoding="utf-8") as data_file_op:
            data_op = data_file_op.read()
            os.unlink(op_file_name_csv)
            self.assertEqual(data_op, expected_op_csvd)
