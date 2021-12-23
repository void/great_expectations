import json
import os
import random

import pytest
from ruamel.yaml import YAML

import great_expectations.exceptions as ge_exceptions
from great_expectations.data_context.util import (
    file_relative_path,
    instantiate_class_from_config,
)

try:
    sqlalchemy = pytest.importorskip("sqlalchemy")
except ImportError:
    sqlalchemy = None

yaml = YAML()


def test_basic_instantiation_with_ConfiguredAssetSqlDataConnector(sa):
    random.seed(0)

    db_file = file_relative_path(
        __file__,
        os.path.join("..", "test_sets", "test_cases_for_sql_data_connector.db"),
    )
    # This is a basic integration test demonstrating an Datasource containing a SQL data_connector
    # It also shows how to instantiate a SQLite SqlAlchemyExecutionEngine
    config = yaml.load(
        f"""
class_name: Datasource

execution_engine:
    class_name: SqlAlchemyExecutionEngine
    connection_string: sqlite:///{db_file}

data_connectors:
    my_sqlite_db:
        class_name: ConfiguredAssetSqlDataConnector

        assets:
            table_partitioned_by_date_column__A:
                splitter_method: _split_on_converted_datetime
                splitter_kwargs:
                    column_name: date
                    date_format_string: "%Y-%W"
    """,
    )

    my_data_source = instantiate_class_from_config(
        config,
        config_defaults={"module_name": "great_expectations.datasource"},
        runtime_environment={"name": "my_sql_datasource"},
    )

    report = my_data_source.self_check()
    # print(json.dumps(report, indent=4))

    report["execution_engine"].pop("connection_string")

    assert report == {
        "execution_engine": {
            "module_name": "great_expectations.execution_engine.sqlalchemy_execution_engine",
            "class_name": "SqlAlchemyExecutionEngine",
        },
        "data_connectors": {
            "count": 1,
            "my_sqlite_db": {
                "class_name": "ConfiguredAssetSqlDataConnector",
                "data_asset_count": 1,
                "example_data_asset_names": ["table_partitioned_by_date_column__A"],
                "data_assets": {
                    "table_partitioned_by_date_column__A": {
                        "batch_definition_count": 5,
                        "example_data_references": [
                            {"date": "2020-00"},
                            {"date": "2020-01"},
                            {"date": "2020-02"},
                        ],
                    }
                },
                "unmatched_data_reference_count": 0,
                "example_unmatched_data_references": [],
                # FIXME: (Sam) example_data_reference removed temporarily in PR #2590:
                # "example_data_reference": {
                #     "batch_spec": {
                #         "table_name": "table_partitioned_by_date_column__A",
                #         "data_asset_name": "table_partitioned_by_date_column__A",
                #         "batch_identifiers": {"date": "2020-01"},
                #         "splitter_method": "_split_on_converted_datetime",
                #         "splitter_kwargs": {
                #             "column_name": "date",
                #             "date_format_string": "%Y-%W",
                #         },
                #     },
                #     "n_rows": 24,
                # },
            },
        },
    }


def test_basic_instantiation_with_InferredAssetSqlDataConnector(sa):
    random.seed(0)

    db_file = file_relative_path(
        __file__,
        os.path.join("..", "test_sets", "test_cases_for_sql_data_connector.db"),
    )
    # This is a basic integration test demonstrating an Datasource containing a SQL data_connector
    # It also shows how to instantiate a SQLite SqlAlchemyExecutionEngine

    config = yaml.load(
        f"""
class_name: Datasource

execution_engine:
    class_name: SqlAlchemyExecutionEngine
    connection_string: sqlite:///{db_file}

data_connectors:
    my_sqlite_db:
        class_name: InferredAssetSqlDataConnector
        name: whole_table
        data_asset_name_prefix: prefix__
        data_asset_name_suffix: __xiffus
    """,
    )

    my_data_source = instantiate_class_from_config(
        config,
        config_defaults={"module_name": "great_expectations.datasource"},
        runtime_environment={"name": "my_sql_datasource"},
    )
    report = my_data_source.self_check()

    connection_string_to_test = f"""sqlite:///{db_file}"""
    assert report == {
        "execution_engine": {
            "connection_string": connection_string_to_test,
            "module_name": "great_expectations.execution_engine.sqlalchemy_execution_engine",
            "class_name": "SqlAlchemyExecutionEngine",
        },
        "data_connectors": {
            "count": 1,
            "my_sqlite_db": {
                "class_name": "InferredAssetSqlDataConnector",
                "data_asset_count": 21,
                "example_data_asset_names": [
                    "prefix__table_containing_id_spacers_for_D__xiffus",
                    "prefix__table_full__I__xiffus",
                    "prefix__table_partitioned_by_date_column__A__xiffus",
                ],
                "data_assets": {
                    "prefix__table_containing_id_spacers_for_D__xiffus": {
                        "batch_definition_count": 1,
                        "example_data_references": [{}],
                    },
                    "prefix__table_full__I__xiffus": {
                        "batch_definition_count": 1,
                        "example_data_references": [{}],
                    },
                    "prefix__table_partitioned_by_date_column__A__xiffus": {
                        "batch_definition_count": 1,
                        "example_data_references": [{}],
                    },
                },
                "unmatched_data_reference_count": 0,
                "example_unmatched_data_references": [],
            },
        },
    }


def test_SimpleSqlalchemyDatasource(empty_data_context):
    context = empty_data_context
    # This test mirrors the likely path to configure a SimpleSqlalchemyDatasource

    db_file = file_relative_path(
        __file__,
        os.path.join("..", "test_sets", "test_cases_for_sql_data_connector.db"),
    )

    # Absolutely minimal starting config
    datasource_with_minimum_config = context.test_yaml_config(
        f"""
class_name: SimpleSqlalchemyDatasource
connection_string: sqlite:///{db_file}
"""
        + """
introspection:
    whole_table: {}
"""
    )
    print(
        json.dumps(
            datasource_with_minimum_config.get_available_data_asset_names(), indent=4
        )
    )

    assert datasource_with_minimum_config.get_available_data_asset_names() == {
        "whole_table": [
            "table_containing_id_spacers_for_D",
            "table_full__I",
            "table_partitioned_by_date_column__A",
            "table_partitioned_by_foreign_key__F",
            "table_partitioned_by_incrementing_batch_id__E",
            "table_partitioned_by_irregularly_spaced_incrementing_id_with_spacing_in_a_second_table__D",
            "table_partitioned_by_multiple_columns__G",
            "table_partitioned_by_regularly_spaced_incrementing_id_column__C",
            "table_partitioned_by_timestamp_column__B",
            "table_that_should_be_partitioned_by_random_hash__H",
            "table_with_fk_reference_from_F",
            "view_by_date_column__A",
            "view_by_incrementing_batch_id__E",
            "view_by_irregularly_spaced_incrementing_id_with_spacing_in_a_second_table__D",
            "view_by_multiple_columns__G",
            "view_by_regularly_spaced_incrementing_id_column__C",
            "view_by_timestamp_column__B",
            "view_containing_id_spacers_for_D",
            "view_partitioned_by_foreign_key__F",
            "view_that_should_be_partitioned_by_random_hash__H",
            "view_with_fk_reference_from_F",
        ]
    }

    assert datasource_with_minimum_config.get_available_data_asset_names_and_types() == {
        "whole_table": [
            ("table_containing_id_spacers_for_D", "table"),
            ("table_full__I", "table"),
            ("table_partitioned_by_date_column__A", "table"),
            ("table_partitioned_by_foreign_key__F", "table"),
            ("table_partitioned_by_incrementing_batch_id__E", "table"),
            (
                "table_partitioned_by_irregularly_spaced_incrementing_id_with_spacing_in_a_second_table__D",
                "table",
            ),
            ("table_partitioned_by_multiple_columns__G", "table"),
            (
                "table_partitioned_by_regularly_spaced_incrementing_id_column__C",
                "table",
            ),
            ("table_partitioned_by_timestamp_column__B", "table"),
            ("table_that_should_be_partitioned_by_random_hash__H", "table"),
            ("table_with_fk_reference_from_F", "table"),
            ("view_by_date_column__A", "view"),
            ("view_by_incrementing_batch_id__E", "view"),
            (
                "view_by_irregularly_spaced_incrementing_id_with_spacing_in_a_second_table__D",
                "view",
            ),
            ("view_by_multiple_columns__G", "view"),
            ("view_by_regularly_spaced_incrementing_id_column__C", "view"),
            ("view_by_timestamp_column__B", "view"),
            ("view_containing_id_spacers_for_D", "view"),
            ("view_partitioned_by_foreign_key__F", "view"),
            ("view_that_should_be_partitioned_by_random_hash__H", "view"),
            ("view_with_fk_reference_from_F", "view"),
        ]
    }

    # Here we should test getting a batch

    # Very thin starting config
    datasource_with_name_suffix = context.test_yaml_config(
        f"""
class_name: SimpleSqlalchemyDatasource
connection_string: sqlite:///{db_file}
"""
        + """
introspection:
    whole_table:
        data_asset_name_suffix: __whole_table
        introspection_directives: {}
"""
    )

    assert datasource_with_name_suffix.get_available_data_asset_names() == {
        "whole_table": [
            "table_containing_id_spacers_for_D__whole_table",
            "table_full__I__whole_table",
            "table_partitioned_by_date_column__A__whole_table",
            "table_partitioned_by_foreign_key__F__whole_table",
            "table_partitioned_by_incrementing_batch_id__E__whole_table",
            "table_partitioned_by_irregularly_spaced_incrementing_id_with_spacing_in_a_second_table__D__whole_table",
            "table_partitioned_by_multiple_columns__G__whole_table",
            "table_partitioned_by_regularly_spaced_incrementing_id_column__C__whole_table",
            "table_partitioned_by_timestamp_column__B__whole_table",
            "table_that_should_be_partitioned_by_random_hash__H__whole_table",
            "table_with_fk_reference_from_F__whole_table",
            "view_by_date_column__A__whole_table",
            "view_by_incrementing_batch_id__E__whole_table",
            "view_by_irregularly_spaced_incrementing_id_with_spacing_in_a_second_table__D__whole_table",
            "view_by_multiple_columns__G__whole_table",
            "view_by_regularly_spaced_incrementing_id_column__C__whole_table",
            "view_by_timestamp_column__B__whole_table",
            "view_containing_id_spacers_for_D__whole_table",
            "view_partitioned_by_foreign_key__F__whole_table",
            "view_that_should_be_partitioned_by_random_hash__H__whole_table",
            "view_with_fk_reference_from_F__whole_table",
        ]
    }

    assert datasource_with_name_suffix.get_available_data_asset_names_and_types() == {
        "whole_table": [
            ("table_containing_id_spacers_for_D", "table"),
            ("table_full__I", "table"),
            ("table_partitioned_by_date_column__A", "table"),
            ("table_partitioned_by_foreign_key__F", "table"),
            ("table_partitioned_by_incrementing_batch_id__E", "table"),
            (
                "table_partitioned_by_irregularly_spaced_incrementing_id_with_spacing_in_a_second_table__D",
                "table",
            ),
            ("table_partitioned_by_multiple_columns__G", "table"),
            (
                "table_partitioned_by_regularly_spaced_incrementing_id_column__C",
                "table",
            ),
            ("table_partitioned_by_timestamp_column__B", "table"),
            ("table_that_should_be_partitioned_by_random_hash__H", "table"),
            ("table_with_fk_reference_from_F", "table"),
            ("view_by_date_column__A", "view"),
            ("view_by_incrementing_batch_id__E", "view"),
            (
                "view_by_irregularly_spaced_incrementing_id_with_spacing_in_a_second_table__D",
                "view",
            ),
            ("view_by_multiple_columns__G", "view"),
            ("view_by_regularly_spaced_incrementing_id_column__C", "view"),
            ("view_by_timestamp_column__B", "view"),
            ("view_containing_id_spacers_for_D", "view"),
            ("view_partitioned_by_foreign_key__F", "view"),
            ("view_that_should_be_partitioned_by_random_hash__H", "view"),
            ("view_with_fk_reference_from_F", "view"),
        ]
    }

    # Here we should test getting a batch

    # Add some manually configured tables...
    datasource_manually_configured = context.test_yaml_config(
        f"""
class_name: SimpleSqlalchemyDatasource
connection_string: sqlite:///{db_file}

introspection:
    whole_table:
        excluded_tables:
            - main.table_partitioned_by_irregularly_spaced_incrementing_id_with_spacing_in_a_second_table__D
            - main.table_partitioned_by_multiple_columns__G
            - main.table_partitioned_by_regularly_spaced_incrementing_id_column__C
            - main.table_partitioned_by_timestamp_column__B
            - main.table_that_should_be_partitioned_by_random_hash__H
            - main.table_with_fk_reference_from_F

    hourly:
        splitter_method: _split_on_converted_datetime
        splitter_kwargs:
            column_name: timestamp
            date_format_string: "%Y-%m-%d:%H"
        included_tables:
            - main.table_partitioned_by_timestamp_column__B
        introspection_directives:
            include_views: true


tables:
    table_partitioned_by_date_column__A:
        partitioners:
            daily:
                data_asset_name_suffix: __daily
                splitter_method: _split_on_converted_datetime
                splitter_kwargs:
                    column_name: date
                    date_format_string: "%Y-%m-%d"
            weekly:
                include_schema_name: False
                data_asset_name_prefix: some_string__
                data_asset_name_suffix: __some_other_string
                splitter_method: _split_on_converted_datetime
                splitter_kwargs:
                    column_name: date
                    date_format_string: "%Y-%W"
            by_id_dozens:
                include_schema_name: True
                # Note: no data_asset_name_suffix
                splitter_method: _split_on_divided_integer
                splitter_kwargs:
                    column_name: id
                    divisor: 12
"""
    )

    print(
        json.dumps(
            datasource_manually_configured.get_available_data_asset_names(), indent=4
        )
    )
    assert datasource_manually_configured.get_available_data_asset_names() == {
        "whole_table": [
            "table_containing_id_spacers_for_D",
            "table_full__I",
            "table_partitioned_by_date_column__A",
            "table_partitioned_by_foreign_key__F",
            "table_partitioned_by_incrementing_batch_id__E",
            "view_by_date_column__A",
            "view_by_incrementing_batch_id__E",
            "view_by_irregularly_spaced_incrementing_id_with_spacing_in_a_second_table__D",
            "view_by_multiple_columns__G",
            "view_by_regularly_spaced_incrementing_id_column__C",
            "view_by_timestamp_column__B",
            "view_containing_id_spacers_for_D",
            "view_partitioned_by_foreign_key__F",
            "view_that_should_be_partitioned_by_random_hash__H",
            "view_with_fk_reference_from_F",
        ],
        "hourly": [
            "table_partitioned_by_timestamp_column__B",
        ],
        "daily": [
            "table_partitioned_by_date_column__A__daily",
        ],
        "weekly": [
            "some_string__table_partitioned_by_date_column__A__some_other_string",
        ],
        "by_id_dozens": [
            "table_partitioned_by_date_column__A",
        ],
    }

    # can't use get_available_data_asset_names_and_types here because it's only implemented
    # on InferredAssetSqlDataConnector, not ConfiguredAssetSqlDataConnector
    with pytest.raises(NotImplementedError):
        datasource_manually_configured.get_available_data_asset_names_and_types()

    # Here we should test getting another batch

    # Drop the introspection...
    datasource_without_introspection = context.test_yaml_config(
        f"""
class_name: SimpleSqlalchemyDatasource
connection_string: sqlite:///{db_file}
"""
        + """
tables:
    table_partitioned_by_date_column__A:
        partitioners:
            whole_table: {}
            daily:
                splitter_method: _split_on_converted_datetime
                splitter_kwargs:
                    column_name: date
                    date_format_string: "%Y-%m-%d"
            weekly:
                splitter_method: _split_on_converted_datetime
                splitter_kwargs:
                    column_name: date
                    date_format_string: "%Y-%W"
            by_id_dozens:
                splitter_method: _split_on_divided_integer
                splitter_kwargs:
                    column_name: id
                    divisor: 12
"""
    )
    print(
        json.dumps(
            datasource_without_introspection.get_available_data_asset_names(), indent=4
        )
    )
    assert datasource_without_introspection.get_available_data_asset_names() == {
        "whole_table": [
            "table_partitioned_by_date_column__A",
        ],
        "daily": [
            "table_partitioned_by_date_column__A",
        ],
        "weekly": [
            "table_partitioned_by_date_column__A",
        ],
        "by_id_dozens": [
            "table_partitioned_by_date_column__A",
        ],
    }

    # Here we should test getting another batch


# Note: Abe 2020111: this test belongs with the data_connector tests, not here.
def test_introspect_db(test_cases_for_sql_data_connector_sqlite_execution_engine):
    # Note: Abe 2020111: this test currently only uses a sqlite fixture.
    # We should extend this to at least include postgresql in the unit tests.
    # Other DBs can be run as integration tests.

    my_data_connector = instantiate_class_from_config(
        config={
            "class_name": "InferredAssetSqlDataConnector",
            "name": "my_test_data_connector",
        },
        runtime_environment={
            "execution_engine": test_cases_for_sql_data_connector_sqlite_execution_engine,
            "datasource_name": "my_test_datasource",
        },
        config_defaults={"module_name": "great_expectations.datasource.data_connector"},
    )

    # print(my_data_connector._introspect_db())
    assert my_data_connector._introspect_db() == [
        {
            "schema_name": "main",
            "table_name": "table_containing_id_spacers_for_D",
            "type": "table",
        },
        {"schema_name": "main", "table_name": "table_full__I", "type": "table"},
        {
            "schema_name": "main",
            "table_name": "table_partitioned_by_date_column__A",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_partitioned_by_foreign_key__F",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_partitioned_by_incrementing_batch_id__E",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_partitioned_by_irregularly_spaced_incrementing_id_with_spacing_in_a_second_table__D",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_partitioned_by_multiple_columns__G",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_partitioned_by_regularly_spaced_incrementing_id_column__C",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_partitioned_by_timestamp_column__B",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_that_should_be_partitioned_by_random_hash__H",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_with_fk_reference_from_F",
            "type": "table",
        },
        {"schema_name": "main", "table_name": "view_by_date_column__A", "type": "view"},
        {
            "schema_name": "main",
            "table_name": "view_by_incrementing_batch_id__E",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_by_irregularly_spaced_incrementing_id_with_spacing_in_a_second_table__D",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_by_multiple_columns__G",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_by_regularly_spaced_incrementing_id_column__C",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_by_timestamp_column__B",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_containing_id_spacers_for_D",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_partitioned_by_foreign_key__F",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_that_should_be_partitioned_by_random_hash__H",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_with_fk_reference_from_F",
            "type": "view",
        },
    ]

    assert my_data_connector._introspect_db(schema_name="main") == [
        {
            "schema_name": "main",
            "table_name": "table_containing_id_spacers_for_D",
            "type": "table",
        },
        {"schema_name": "main", "table_name": "table_full__I", "type": "table"},
        {
            "schema_name": "main",
            "table_name": "table_partitioned_by_date_column__A",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_partitioned_by_foreign_key__F",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_partitioned_by_incrementing_batch_id__E",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_partitioned_by_irregularly_spaced_incrementing_id_with_spacing_in_a_second_table__D",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_partitioned_by_multiple_columns__G",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_partitioned_by_regularly_spaced_incrementing_id_column__C",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_partitioned_by_timestamp_column__B",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_that_should_be_partitioned_by_random_hash__H",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_with_fk_reference_from_F",
            "type": "table",
        },
        {"schema_name": "main", "table_name": "view_by_date_column__A", "type": "view"},
        {
            "schema_name": "main",
            "table_name": "view_by_incrementing_batch_id__E",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_by_irregularly_spaced_incrementing_id_with_spacing_in_a_second_table__D",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_by_multiple_columns__G",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_by_regularly_spaced_incrementing_id_column__C",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_by_timestamp_column__B",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_containing_id_spacers_for_D",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_partitioned_by_foreign_key__F",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_that_should_be_partitioned_by_random_hash__H",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_with_fk_reference_from_F",
            "type": "view",
        },
    ]

    assert my_data_connector._introspect_db(schema_name="waffle") == []

    # This is a weak test, since this db doesn't have any additional schemas or system tables to show.
    assert my_data_connector._introspect_db(
        ignore_information_schemas_and_system_tables=False
    ) == [
        {
            "schema_name": "main",
            "table_name": "table_containing_id_spacers_for_D",
            "type": "table",
        },
        {"schema_name": "main", "table_name": "table_full__I", "type": "table"},
        {
            "schema_name": "main",
            "table_name": "table_partitioned_by_date_column__A",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_partitioned_by_foreign_key__F",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_partitioned_by_incrementing_batch_id__E",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_partitioned_by_irregularly_spaced_incrementing_id_with_spacing_in_a_second_table__D",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_partitioned_by_multiple_columns__G",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_partitioned_by_regularly_spaced_incrementing_id_column__C",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_partitioned_by_timestamp_column__B",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_that_should_be_partitioned_by_random_hash__H",
            "type": "table",
        },
        {
            "schema_name": "main",
            "table_name": "table_with_fk_reference_from_F",
            "type": "table",
        },
        {"schema_name": "main", "table_name": "view_by_date_column__A", "type": "view"},
        {
            "schema_name": "main",
            "table_name": "view_by_incrementing_batch_id__E",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_by_irregularly_spaced_incrementing_id_with_spacing_in_a_second_table__D",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_by_multiple_columns__G",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_by_regularly_spaced_incrementing_id_column__C",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_by_timestamp_column__B",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_containing_id_spacers_for_D",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_partitioned_by_foreign_key__F",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_that_should_be_partitioned_by_random_hash__H",
            "type": "view",
        },
        {
            "schema_name": "main",
            "table_name": "view_with_fk_reference_from_F",
            "type": "view",
        },
    ]


def test_skip_inapplicable_tables(empty_data_context):
    context = empty_data_context
    # This test mirrors the likely path to configure a SimpleSqlalchemyDatasource

    db_file = file_relative_path(
        __file__,
        os.path.join("..", "test_sets", "test_cases_for_sql_data_connector.db"),
    )

    my_sql_datasource = context.test_yaml_config(
        f"""
class_name: SimpleSqlalchemyDatasource
connection_string: sqlite:///{db_file}
introspection:
    daily:
        skip_inapplicable_tables: true
        splitter_method: _split_on_converted_datetime
        splitter_kwargs:
            column_name: date
            date_format_string: "%Y-%m-%d"
"""
    )
    print(json.dumps(my_sql_datasource.get_available_data_asset_names(), indent=4))

    assert my_sql_datasource.get_available_data_asset_names() == {
        "daily": [
            "table_containing_id_spacers_for_D",
            "table_full__I",
            "table_partitioned_by_date_column__A",
            "table_with_fk_reference_from_F",
            "view_by_date_column__A",
            "view_with_fk_reference_from_F",
        ]
    }

    with pytest.raises(ge_exceptions.DatasourceInitializationError):
        # noinspection PyUnusedLocal
        my_sql_datasource = context.test_yaml_config(
            f"""
class_name: SimpleSqlalchemyDatasource
connection_string: sqlite:///{db_file}
introspection:
    daily:
        skip_inapplicable_tables: false
        splitter_method: _split_on_converted_datetime
        splitter_kwargs:
            column_name: date
            date_format_string: "%Y-%m-%d"
    """
        )
