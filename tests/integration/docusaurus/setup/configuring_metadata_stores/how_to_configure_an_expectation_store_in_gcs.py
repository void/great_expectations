import os
import subprocess

from ruamel import yaml

import great_expectations as ge

context = ge.get_context()

# parse great_expectations.yml for comparison
great_expectations_yaml_file_path = os.path.join(
    context.root_directory, "great_expectations.yml"
)
with open(great_expectations_yaml_file_path, "r") as f:
    great_expectations_yaml = yaml.safe_load(f)

stores = great_expectations_yaml["stores"]
pop_stores = ["checkpoint_store", "evaluation_parameter_store", "validations_store"]
for store in pop_stores:
    stores.pop(store)

actual_existing_expectations_store = {}
actual_existing_expectations_store["stores"] = stores
actual_existing_expectations_store["expectations_store_name"] = great_expectations_yaml[
    "expectations_store_name"
]

expected_existing_expectations_store_yaml = """
stores:
  expectations_store:
    class_name: ExpectationsStore
    store_backend:
      class_name: TupleFilesystemStoreBackend
      base_directory: expectations/

expectations_store_name: expectations_store
"""

assert actual_existing_expectations_store == yaml.safe_load(
    expected_existing_expectations_store_yaml
)

configured_expectations_store_yaml = """
stores:
  expectations_GCS_store:
    class_name: ExpectationsStore
    store_backend:
      class_name: TupleGCSStoreBackend
      project: <YOUR GCP PROJECT NAME>
      bucket: <YOUR GCS BUCKET NAME>
      prefix: <YOUR GCS PREFIX NAME>

expectations_store_name: expectations_GCS_store
"""

# replace example code with integration test configuration
configured_expectations_store = yaml.safe_load(configured_expectations_store_yaml)
configured_expectations_store["stores"]["expectations_GCS_store"]["store_backend"][
    "project"
] = "superconductive-internal"
configured_expectations_store["stores"]["expectations_GCS_store"]["store_backend"][
    "bucket"
] = "superconductive-integration-tests"
configured_expectations_store["stores"]["expectations_GCS_store"]["store_backend"][
    "prefix"
] = "how_to_configure_an_expectation_store_in_gcs/expectations"

try:
    # remove this bucket if there was a failure in the script last time
    result = subprocess.run(
        "gsutil rm -r gs://superconductive-integration-tests/how_to_configure_an_expectation_store_in_gcs/expectations".split(),
        check=True,
        stderr=subprocess.PIPE,
    )
except Exception as e:
    pass

# add and set the new expectation store
context.add_store(
    store_name=configured_expectations_store["expectations_store_name"],
    store_config=configured_expectations_store["stores"]["expectations_GCS_store"],
)
with open(great_expectations_yaml_file_path, "r") as f:
    great_expectations_yaml = yaml.safe_load(f)
great_expectations_yaml["expectations_store_name"] = "expectations_GCS_store"
great_expectations_yaml["stores"]["expectations_GCS_store"]["store_backend"].pop(
    "suppress_store_backend_id"
)
with open(great_expectations_yaml_file_path, "w") as f:
    yaml.dump(great_expectations_yaml, f, default_flow_style=False)

expectation_suite_name = "my_expectation_suite"
context.create_expectation_suite(expectation_suite_name=expectation_suite_name)

# try gsutil cp command
copy_expectation_command = """
gsutil cp expectations/my_expectation_suite.json gs://<YOUR GCS BUCKET NAME>/<YOUR GCS PREFIX NAME>/my_expectation_suite.json
"""

local_expectation_suite_file_path = os.path.join(
    context.root_directory, "expectations", f"{expectation_suite_name}.json"
)
copy_expectation_command = copy_expectation_command.replace(
    "expectations/my_expectation_suite.json", local_expectation_suite_file_path
)
copy_expectation_command = copy_expectation_command.replace(
    "<YOUR GCS BUCKET NAME>",
    configured_expectations_store["stores"]["expectations_GCS_store"]["store_backend"][
        "bucket"
    ],
)
copy_expectation_command = copy_expectation_command.replace(
    "<YOUR GCS PREFIX NAME>/my_expectation_suite.json",
    configured_expectations_store["stores"]["expectations_GCS_store"]["store_backend"][
        "prefix"
    ]
    + f"/{expectation_suite_name}.json",
)

result = subprocess.run(
    copy_expectation_command.strip().split(),
    check=True,
    stderr=subprocess.PIPE,
)
stderr = result.stderr.decode("utf-8")

copy_expectation_output = """
Operation completed over 1 objects
"""

assert copy_expectation_output.strip() in stderr

# list expectation stores
list_expectation_stores_command = """
great_expectations --v3-api store list
"""

result = subprocess.run(
    list_expectation_stores_command.strip().split(),
    check=True,
    stdout=subprocess.PIPE,
)
stdout = result.stdout.decode("utf-8")

list_expectation_stores_output = """
  - name: expectations_GCS_store
    class_name: ExpectationsStore
    store_backend:
      class_name: TupleGCSStoreBackend
      project: <YOUR GCP PROJECT NAME>
      bucket: <YOUR GCS BUCKET NAME>
      prefix: <YOUR GCS PREFIX NAME>
"""

assert "expectations_GCS_store" in list_expectation_stores_output
assert "expectations_GCS_store" in stdout
assert "TupleGCSStoreBackend" in list_expectation_stores_output
assert "TupleGCSStoreBackend" in stdout

# list expectation suites
list_expectation_suites_command = """
great_expectations --v3-api suite list
"""

result = subprocess.run(
    list_expectation_suites_command.strip().split(),
    check=True,
    stdout=subprocess.PIPE,
)
stdout = result.stdout.decode("utf-8")

list_expectation_suites_output = """
1 Expectation Suite found:
 - my_expectation_suite
"""

assert "1 Expectation Suite found:" in list_expectation_suites_output
assert "1 Expectation Suite found:" in stdout
assert "my_expectation_suite" in list_expectation_suites_output
assert "my_expectation_suite" in stdout

# clean up this bucket for next time
result = subprocess.run(
    "gsutil rm -r gs://superconductive-integration-tests/how_to_configure_an_expectation_store_in_gcs/expectations".split(),
    check=True,
    stderr=subprocess.PIPE,
)
