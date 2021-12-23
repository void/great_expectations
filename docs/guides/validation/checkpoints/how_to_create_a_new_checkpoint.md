---
title: How to create a new Checkpoint
---

This guide will help you create a new Checkpoint, which allows you to couple an Expectation Suite with a data set to validate.

Note: As of Great Expectations version 0.13.7, we have updated and improved the Checkpoints feature. You can continue to use your existing legacy Checkpoint workflows if you’re working with concepts from the Batch Kwargs (v2) API. If you’re using concepts from the BatchRequest (v3) API, please refer to the new Checkpoints guides.

### Steps for Checkpoints (>=0.13.12)

:::note Prerequisites: 

This how-to guide assumes you have already:

* [Set up a working deployment of Great Expectations](/docs/tutorials/getting_started/intro)
* [Configured a Datasource using the BatchRequest (v3) API](/docs/tutorials/getting_started/connect_to_data)
* [Created an Expectation Suite](/docs/tutorials/getting_started/create_your_first_expectations)

:::

##### 1. First, run the CLI command below.

````console
great_expectations --v3-api checkpoint new my_checkpoint
````

##### 2.  Next, you will be presented with a Jupyter Notebook which will guide you through the steps of creating a checkpoint.

### Additional Notes

Within this notebook, you will have the opportunity to create your own yaml Checkpoint configuration. The following text walks through an example.

#### SimpleCheckpoint Example

##### 2a. Here is a simple example configuration. 

For this example, we’ll demonstrate using a basic Checkpoint configuration with the `SimpleCheckpoint` class, which takes care of some defaults. Replace all names such as `my_datasource` with the respective DataSource, DataConnector, DataAsset, and Expectation Suite names you have configured in your `great_expectations.yml`.

````yaml
config = """
name: my_checkpoint
config_version: 1
class_name: SimpleCheckpoint
validations:
  - batch_request:
      datasource_name: my_datasource
      data_connector_name: my_data_connector
      data_asset_name: MyDataAsset
      data_connector_query:
        index: -1
    expectation_suite_name: my_suite
"""
````

This is the minimum required to configure a Checkpoint that will run the Expectation Suite `my_suite` against the data asset `MyDataAsset`. See [How to configure a new Checkpoint using test_yaml_config](/docs/guides/validation/checkpoints/how_to_configure_a_new_checkpoint_using_test_yaml_config) for advanced configuration options.

##### 2b. Test your config using `context.test_yaml_config`.

````python
context.test_yaml_config(yaml_config=config)
````

When executed, test_yaml_config will instantiate the component and run through a self_check procedure to verify that the component works as expected.

In the case of a Checkpoint, this means

1. validating the yaml configuration,
2. verifying that the Checkpoint class with the given configuration, if valid, can be instantiated, and
3. printing warnings in case certain parts of the configuration, while valid, may be incomplete and need to be better specified for a successful Checkpoint operation.

The output will look something like this:

````console
Attempting to instantiate class from config...
Instantiating as a SimpleCheckpoint, since class_name is SimpleCheckpoint
Successfully instantiated SimpleCheckpoint


Checkpoint class name: SimpleCheckpoint
````

If something about your configuration wasn’t set up correctly, `test_yaml_config` will raise an error.

##### 2c. Store your Checkpoint config.

After you are satisfied with your configuration, save it by running the appropriate cells in the Jupyter Notebook.

##### 2d. (Optional:) Check your stored Checkpoint config.

If the Store Backend of your Checkpoint Store is on the local filesystem, you can navigate to the `checkpoints` store directory that is configured in `great_expectations.yml` and find the configuration files corresponding to the Checkpoints you created.

##### 2e. (Optional:) Test run the new Checkpoint and open Data Docs.

Now that you have stored your Checkpoint configuration to the Store backend configured for the Checkpoint Configuration store of your Data Context, you can also test `context.run_checkpoint`, right within your Jupyter Notebook by running the appropriate cells.

Before running a Checkpoint, make sure that all classes and Expectation Suites referred to in the configuration exist.

When `run_checkpoint` returns, the `checkpoint_run_result` can then be checked for the value of the `success` field (all validations passed) and other information associated with running the specified actions.

For more advanced configurations of Checkpoints, please see [How to configure a new Checkpoint using test_yaml_config](/docs/guides/validation/checkpoints/how_to_configure_a_new_checkpoint_using_test_yaml_config).

### Additional Resources

* [How to configure a new Checkpoint using test_yaml_config](/docs/guides/validation/checkpoints/how_to_configure_a_new_checkpoint_using_test_yaml_config/)
* [How to add validations data or suites to a Checkpoint](/docs/guides/validation/checkpoints/how_to_add_validations_data_or_suites_to_a_checkpoint/)
