import logging

import pytest

from great_expectations import DataContext
from great_expectations.core.usage_statistics.schemas import (
    anonymized_usage_statistics_record_schema,
)
from great_expectations.core.usage_statistics.usage_statistics import (
    UsageStatisticsHandler,
)
from great_expectations.data_context import BaseDataContext
from great_expectations.data_context.types.base import DataContextConfig
from tests.core.usage_statistics.util import usage_stats_invalid_messages_exist
from tests.integration.usage_statistics.test_integration_usage_statistics import (
    USAGE_STATISTICS_QA_URL,
)


@pytest.fixture
def in_memory_data_context_config_usage_stats_enabled():

    return DataContextConfig(
        **{
            "commented_map": {},
            "config_version": 2,
            "plugins_directory": None,
            "evaluation_parameter_store_name": "evaluation_parameter_store",
            "validations_store_name": "validations_store",
            "expectations_store_name": "expectations_store",
            "config_variables_file_path": None,
            "datasources": {},
            "stores": {
                "expectations_store": {
                    "class_name": "ExpectationsStore",
                },
                "validations_store": {
                    "class_name": "ValidationsStore",
                },
                "evaluation_parameter_store": {
                    "class_name": "EvaluationParameterStore",
                },
            },
            "data_docs_sites": {},
            "validation_operators": {
                "default": {
                    "class_name": "ActionListValidationOperator",
                    "action_list": [],
                }
            },
            "anonymous_usage_statistics": {
                "enabled": True,
                "data_context_id": "00000000-0000-0000-0000-000000000001",
                "usage_statistics_url": USAGE_STATISTICS_QA_URL,
            },
        }
    )


@pytest.fixture
def sample_partial_message():
    return {
        "event": "checkpoint.run",
        "event_payload": {
            "anonymized_name": "f563d9aa1604e16099bb7dff7b203319",
            "config_version": 1.0,
            "anonymized_expectation_suite_name": "6a04fc37da0d43a4c21429f6788d2cff",
            "anonymized_action_list": [
                {
                    "anonymized_name": "8e3e134cd0402c3970a02f40d2edfc26",
                    "parent_class": "StoreValidationResultAction",
                },
                {
                    "anonymized_name": "40e24f0c6b04b6d4657147990d6f39bd",
                    "parent_class": "StoreEvaluationParametersAction",
                },
                {
                    "anonymized_name": "2b99b6b280b8a6ad1176f37580a16411",
                    "parent_class": "UpdateDataDocsAction",
                },
            ],
            "anonymized_validations": [
                {
                    "anonymized_batch_request": {
                        "anonymized_batch_request_required_top_level_properties": {
                            "anonymized_datasource_name": "a732a247720783a5931fa7c4606403c2",
                            "anonymized_data_connector_name": "d52d7bff3226a7f94dd3510c1040de78",
                            "anonymized_data_asset_name": "556e8c06239d09fc66f424eabb9ca491",
                        },
                        "batch_request_optional_top_level_keys": [
                            "batch_identifiers",
                            "runtime_parameters",
                        ],
                        "runtime_parameters_keys": ["batch_data"],
                    },
                    "anonymized_expectation_suite_name": "6a04fc37da0d43a4c21429f6788d2cff",
                    "anonymized_action_list": [
                        {
                            "anonymized_name": "8e3e134cd0402c3970a02f40d2edfc26",
                            "parent_class": "StoreValidationResultAction",
                        },
                        {
                            "anonymized_name": "40e24f0c6b04b6d4657147990d6f39bd",
                            "parent_class": "StoreEvaluationParametersAction",
                        },
                        {
                            "anonymized_name": "2b99b6b280b8a6ad1176f37580a16411",
                            "parent_class": "UpdateDataDocsAction",
                        },
                    ],
                },
            ],
        },
        "success": True,
        # "version": "1.0.0",
        # "event_time": "2020-06-25T16:08:28.070Z",
        # "event_duration": 123,
        # "data_context_id": "00000000-0000-0000-0000-000000000002",
        # "data_context_instance_id": "10000000-0000-0000-0000-000000000002",
        # "ge_version": "0.13.45.manual_testing",
        "x-forwarded-for": "00.000.00.000, 00.000.000.000",
    }


def test_usage_statistics_handler_build_envelope(
    in_memory_data_context_config_usage_stats_enabled, sample_partial_message
):
    """This test is for a happy path only but will fail if there is an exception thrown in build_envelope"""

    context: BaseDataContext = BaseDataContext(
        in_memory_data_context_config_usage_stats_enabled
    )

    usage_statistics_handler = UsageStatisticsHandler(
        data_context=context,
        data_context_id=in_memory_data_context_config_usage_stats_enabled.anonymous_usage_statistics.data_context_id,
        usage_statistics_url=in_memory_data_context_config_usage_stats_enabled.anonymous_usage_statistics.usage_statistics_url,
    )

    assert (
        usage_statistics_handler._data_context_id
        == "00000000-0000-0000-0000-000000000001"
    )

    envelope = usage_statistics_handler.build_envelope(sample_partial_message)
    required_keys = [
        "event",
        "event_payload",
        "version",
        "ge_version",
        "data_context_id",
        "data_context_instance_id",
        "event_time",
    ]
    assert all([key in envelope.keys() for key in required_keys])

    assert envelope["version"] == "1.0.0"
    assert envelope["data_context_id"] == "00000000-0000-0000-0000-000000000001"


def test_usage_statistics_handler_validate_message_failure(
    caplog, in_memory_data_context_config_usage_stats_enabled, sample_partial_message
):

    # caplog default is WARNING and above, we want to see DEBUG level messages for this test
    caplog.set_level(
        level=logging.DEBUG,
        logger="great_expectations.core.usage_statistics.usage_statistics",
    )

    context: BaseDataContext = BaseDataContext(
        in_memory_data_context_config_usage_stats_enabled
    )

    usage_statistics_handler = UsageStatisticsHandler(
        data_context=context,
        data_context_id=in_memory_data_context_config_usage_stats_enabled.anonymous_usage_statistics.data_context_id,
        usage_statistics_url=in_memory_data_context_config_usage_stats_enabled.anonymous_usage_statistics.usage_statistics_url,
    )

    assert (
        usage_statistics_handler._data_context_id
        == "00000000-0000-0000-0000-000000000001"
    )

    validated_message = usage_statistics_handler.validate_message(
        sample_partial_message, anonymized_usage_statistics_record_schema
    )
    assert not validated_message
    assert usage_stats_invalid_messages_exist(caplog.messages)


def test_usage_statistics_handler_validate_message_success(
    caplog, in_memory_data_context_config_usage_stats_enabled, sample_partial_message
):

    # caplog default is WARNING and above, we want to see DEBUG level messages for this test
    caplog.set_level(
        level=logging.DEBUG,
        logger="great_expectations.core.usage_statistics.usage_statistics",
    )

    context: BaseDataContext = BaseDataContext(
        in_memory_data_context_config_usage_stats_enabled
    )

    usage_statistics_handler = UsageStatisticsHandler(
        data_context=context,
        data_context_id=in_memory_data_context_config_usage_stats_enabled.anonymous_usage_statistics.data_context_id,
        usage_statistics_url=in_memory_data_context_config_usage_stats_enabled.anonymous_usage_statistics.usage_statistics_url,
    )

    assert (
        usage_statistics_handler._data_context_id
        == "00000000-0000-0000-0000-000000000001"
    )

    envelope = usage_statistics_handler.build_envelope(sample_partial_message)
    validated_message = usage_statistics_handler.validate_message(
        envelope, anonymized_usage_statistics_record_schema
    )

    assert validated_message
    assert not usage_stats_invalid_messages_exist(caplog.messages)


def test_build_init_payload(
    titanic_pandas_data_context_with_v013_datasource_with_checkpoints_v1_with_empty_store_stats_enabled,
):
    """This test is for a happy path only but will fail if there is an exception thrown in init_payload"""

    context: DataContext = titanic_pandas_data_context_with_v013_datasource_with_checkpoints_v1_with_empty_store_stats_enabled
    usage_statistics_handler = context._usage_statistics_handler
    init_payload = usage_statistics_handler.build_init_payload()
    assert list(init_payload.keys()) == [
        "platform.system",
        "platform.release",
        "version_info",
        "anonymized_datasources",
        "anonymized_stores",
        "anonymized_validation_operators",
        "anonymized_data_docs_sites",
        "anonymized_expectation_suites",
    ]
    assert init_payload["anonymized_datasources"] == [
        {
            "anonymized_data_connectors": [
                {
                    "anonymized_name": "af09acd176f54642635a8a2975305437",
                    "parent_class": "InferredAssetFilesystemDataConnector",
                },
                {
                    "anonymized_name": "e475f70ca0bcbaf2748b93da5e9867ec",
                    "parent_class": "ConfiguredAssetFilesystemDataConnector",
                },
                {
                    "anonymized_name": "2030a96b1eaa8579087d31709fb6ec1b",
                    "parent_class": "ConfiguredAssetFilesystemDataConnector",
                },
                {
                    "anonymized_name": "d52d7bff3226a7f94dd3510c1040de78",
                    "parent_class": "RuntimeDataConnector",
                },
            ],
            "anonymized_execution_engine": {
                "anonymized_name": "212039ff9860a796a32c75c7d5c2fac0",
                "parent_class": "PandasExecutionEngine",
            },
            "anonymized_name": "a732a247720783a5931fa7c4606403c2",
            "parent_class": "Datasource",
        }
    ]
    assert init_payload["anonymized_expectation_suites"] == []
