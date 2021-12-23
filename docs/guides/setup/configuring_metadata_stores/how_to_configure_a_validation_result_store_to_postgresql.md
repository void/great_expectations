---
title: How to configure a Validation Result store to PostgreSQL
---
import Prerequisites from '../../connecting_to_your_data/components/prerequisites.jsx'

By default, Validations are stored in JSON format in the ``uncommitted/validations/`` subdirectory of your ``great_expectations/`` folder.  Since Validations may include examples of data (which could be sensitive or regulated) they should not be committed to a source control system.  This guide will help you configure Great Expectations to store them in a PostgreSQL database.

<Prerequisites>

- Configured a [Data Context](../../../tutorials/getting_started/initialize_a_data_context.md).
- Configured an [Expectations Suite](../../../tutorials/getting_started/create_your_first_expectations.md).
- Configured a [Checkpoint](../../../tutorials/getting_started/validate_your_data.md).
- Configured a [PostgreSQL](https://www.postgresql.org/) database with appropriate credentials.

</Prerequisites>

Steps
-----

1. **Configure the** ``config_variables.yml`` **file with your database credentials**

    We recommend that database credentials be stored in the ``config_variables.yml`` file, which is located in the ``uncommitted/`` folder by default, and is not part of source control. The following lines add database credentials under the key ``db_creds``. Additional options for configuring the ``config_variables.yml`` file or additional environment variables can be found [here](../configuring_data_contexts/how_to_configure_credentials.md).

    ```yaml
    db_creds:
        drivername: postgres
        host: '<your_host_name>'
        port: '<your_port>'
        username: '<your_username>'
        password: '<your_password>'
        database: '<your_database_name>'
    ```

    It is also possible to specify `schema` as an additional keyword argument if you would like to use a specific schema as the backend, but this is entirely optional.

    ```yaml
    db_creds:
        drivername: postgres
        host: '<your_host_name>'
        port: '<your_port>'
        username: '<your_username>'
        password: '<your_password>'
        database: '<your_database_name>'
        schema: '<your_schema_name>'
    ```

2. **Identify your Data Context Validations Store**

    In your ``great_expectations.yml``, look for the following lines.  The configuration tells Great Expectations to look for Validations in a store called ``validations_store``. The ``base_directory`` for ``validations_store`` is set to ``uncommitted/validations/`` by default.

    ```yaml
    validations_store_name: validations_store

    stores:
        validations_store:
            class_name: ValidationsStore
            store_backend:
                class_name: TupleFilesystemStoreBackend
                base_directory: uncommitted/validations/
    ```

3. **Update your configuration file to include a new store for Validations on PostgreSQL**

    In our case, the name is set to ``validations_postgres_store``, but it can be any name you like.  We also need to make some changes to the ``store_backend`` settings.  The ``class_name`` will be set to ``DatabaseStoreBackend``, and ``credentials`` will be set to ``${db_creds}``, which references the corresponding key in the ``config_variables.yml`` file.

    ```yaml
    validations_store_name: validations_postgres_store

    stores:
        validations_postgres_store:
            class_name: ValidationsStore
            store_backend:
                class_name: DatabaseStoreBackend
                credentials: ${db_creds}
    ```


5. **Confirm that the new Validations store has been added by running** ``great_expectations --v3-api store list``.

    Notice the output contains two Validation stores: the original ``validations_store`` on the local filesystem and the ``validations_postgres_store`` we just configured.  This is ok, since Great Expectations will look for Validations in PostgreSQL as long as we set the ``validations_store_name`` variable to ``validations_postgres_store``. The config for ``validations_store`` can be removed if you would like.

    ```bash
    great_expectations --v3-api store list

    - name: validations_store
    class_name: ValidationsStore
    store_backend:
        class_name: TupleFilesystemStoreBackend
        base_directory: uncommitted/validations/

    - name: validations_postgres_store
    class_name: ValidationsStore
    store_backend:
        class_name: DatabaseStoreBackend
        credentials:
            database: '<your_db_name>'
            drivername: postgresql
            host: '<your_host_name>'
            password: ******
            port: '<your_port>'
            username: '<your_username>'
    ```

6. **Confirm that the Validations store has been correctly configured.**

    Run a [Checkpoint](../../../tutorials/getting_started/validate_your_data.md) to store results in the new Validations store in PostgreSQL then visualize the results by re-building [Data Docs](../../../tutorials/getting_started/check_out_data_docs.md).

    Behind the scenes, Great Expectations will create a new table in your database called ``ge_validations_store``, and populate the fields with information from the Validation results.


If it would be useful to you, please comment with a +1 and feel free to add any suggestions or questions below.

Also, please reach out to us on [Slack](https://greatexpectations.io/slack) if you would like to learn more, or have any questions.
