---
title: How to update Data Docs as a Validation Action
---

import Prerequisites from '../../../guides/connecting_to_your_data/components/prerequisites.jsx';

This guide will explain how to use a Validation Action to update Data Docs sites with new Validation Results from Validation Operator runs.

<Prerequisites>

  - Set up a `.py` class: `great_expectations.validation_operators.validation_operators.ActionListValidationOperator` **or**
 - Set up a `.py` class: `great_expectations.validation_operators.validation_operators.WarningAndFailureExpectationSuitesValidationOperator`
 - Created at least one Expectation Suite.
 - Created at least one [Checkpoint](../checkpoints/how_to_create_a_new_checkpoint). You will need it in order to test that your new Validation Operator is working.

</Prerequisites>

Steps
------

1. **Update the action_list key in your Validation Operator config.**

   Add the ``UpdateDataDocsAction`` action to the ``action_list`` key of the ``ActionListValidationOperator`` or ``WarningAndFailureExpectationSuitesValidationOperator`` config in your ``great_expectations.yml``. This action will update all configured Data Docs sites with the new validation from the Validation Operator run.

   :::note Note:
   The ``StoreValidationResultAction`` action must appear before this action, since Data Docs are rendered from Validation Results from the store.
   :::

   ```yaml
   validation_operators:
     action_list_operator: # this is a user-selected name
       class_name: ActionListValidationOperator
       action_list:
       - name: store_validation_result # this is a user-selected name
         action:
           class_name: StoreValidationResultAction
       - name: update_data_docs # this is a user-selected name
         action:
           class_name: UpdateDataDocsAction
   ```

2. **If you only want to update certain configured Data Docs sites**:

   - Add a ``site_names`` key to the ``UpdateDataDocsAction`` config.

   ```yaml
   validation_operators:
     action_list_operator: # this is a user-selected name
       class_name: ActionListValidationOperator
       action_list:
       - name: store_validation_result # this is a user-selected name
         action:
           class_name: StoreValidationResultAction
       - name: update_data_docs # this is a user-selected name
         action:
           class_name: UpdateDataDocsAction
           site_names:
             - team_site
   ```

3. **Test your configuration.**

   Test that your new Validation Operator Action is configured correctly:

   1. Open the configuration file of a Checkpoint you created earlier and replace the value of ``validation_operator_name`` with the name of the Validation Operator you added the ``UpdateDataDocs`` action to. The details of Checkpoint configuration can be found in this [How to add validations data or suites to a Checkpoint](../../../guides/validation/checkpoints/how_to_add_validations_data_or_suites_to_a_checkpoint).
   2. Run the Checkpoint and verify that no errors are thrown. You can run the Checkpoint from the CLI or using Python as explained in [How to validate your data using a Checkpoint](../how_to_validate_data_by_running_a_checkpoint.md).
   3. Check your configured Data Docs sites to confirm that a new Validation Result has been added.

Additional notes
----------------

The ``UpdateDataDocsAction`` generates an HTML file for the latest Validation Result and updates the index page to link to the new file, and re-renders pages for the suite used for that validation. It does not perform a full rebuild of Data Docs sites. This means that if you wish to render older Validation Results, you should run full Data Docs rebuild (via CLI's ``great_expectations docs build`` command or by calling ``context.build_data_docs()``).


Additional resources
--------------------

- [Checkpoints and Actions](../../../reference/checkpoints_and_actions)
