import datetime
import itertools
import os
import uuid
from typing import List, Optional, Union

import great_expectations.exceptions as ge_exceptions
from great_expectations.checkpoint import Checkpoint, LegacyCheckpoint, SimpleCheckpoint
from great_expectations.checkpoint.types.checkpoint_result import CheckpointResult
from great_expectations.core.batch import BatchRequest, get_batch_request_dict
from great_expectations.data_context.store import CheckpointStore
from great_expectations.data_context.types.base import (
    CheckpointConfig,
    DataContextConfigDefaults,
)
from great_expectations.data_context.types.refs import GeCloudIdAwareRef
from great_expectations.data_context.types.resource_identifiers import (
    ConfigurationIdentifier,
    GeCloudIdentifier,
)
from great_expectations.data_context.util import instantiate_class_from_config
from great_expectations.marshmallow__shade import ValidationError
from great_expectations.util import filter_properties_dict


def list_checkpoints(
    checkpoint_store: CheckpointStore,
    ge_cloud_mode: bool,
) -> List[str]:
    if ge_cloud_mode:
        return checkpoint_store.list_keys()

    return [x.configuration_key for x in checkpoint_store.list_keys()]


def add_checkpoint(
    data_context: "DataContext",  # noqa: F821
    checkpoint_store: CheckpointStore,
    checkpoint_store_name: str,
    ge_cloud_mode: bool,
    name: str,
    config_version: Optional[Union[int, float]] = None,
    template_name: Optional[str] = None,
    module_name: Optional[str] = None,
    class_name: Optional[str] = None,
    run_name_template: Optional[str] = None,
    expectation_suite_name: Optional[str] = None,
    batch_request: Optional[Union[BatchRequest, dict]] = None,
    action_list: Optional[List[dict]] = None,
    evaluation_parameters: Optional[dict] = None,
    runtime_configuration: Optional[dict] = None,
    validations: Optional[List[dict]] = None,
    profilers: Optional[List[dict]] = None,
    # Next two fields are for LegacyCheckpoint configuration
    validation_operator_name: Optional[str] = None,
    batches: Optional[List[dict]] = None,
    # the following four arguments are used by SimpleCheckpoint
    site_names: Optional[Union[str, List[str]]] = None,
    slack_webhook: Optional[str] = None,
    notify_on: Optional[str] = None,
    notify_with: Optional[Union[str, List[str]]] = None,
    ge_cloud_id: Optional[str] = None,
    expectation_suite_ge_cloud_id: Optional[str] = None,
) -> Union[Checkpoint, LegacyCheckpoint]:

    batch_request, validations = get_batch_request_dict(batch_request, validations)

    checkpoint_config: Union[CheckpointConfig, dict]

    checkpoint_config = {
        "name": name,
        "config_version": config_version,
        "template_name": template_name,
        "module_name": module_name,
        "class_name": class_name,
        "run_name_template": run_name_template,
        "expectation_suite_name": expectation_suite_name,
        "batch_request": batch_request,
        "action_list": action_list,
        "evaluation_parameters": evaluation_parameters,
        "runtime_configuration": runtime_configuration,
        "validations": validations,
        "profilers": profilers,
        # Next two fields are for LegacyCheckpoint configuration
        "validation_operator_name": validation_operator_name,
        "batches": batches,
        # the following four keys are used by SimpleCheckpoint
        "site_names": site_names,
        "slack_webhook": slack_webhook,
        "notify_on": notify_on,
        "notify_with": notify_with,
        "ge_cloud_id": ge_cloud_id,
        "expectation_suite_ge_cloud_id": expectation_suite_ge_cloud_id,
    }

    # DataFrames shouldn't be saved to CheckpointStore
    if checkpoint_config.get("validations") is not None:
        for idx, val in enumerate(checkpoint_config["validations"]):
            if (
                val.get("batch_request") is not None
                and val["batch_request"].get("runtime_parameters") is not None
                and val["batch_request"]["runtime_parameters"].get("batch_data")
                is not None
            ):
                raise ge_exceptions.InvalidConfigError(
                    f'batch_data found in validations at index {idx} cannot be saved to CheckpointStore "{checkpoint_store_name}"'
                )
    elif (
        checkpoint_config.get("batch_request") is not None
        and checkpoint_config["batch_request"].get("runtime_parameters") is not None
        and checkpoint_config["batch_request"]["runtime_parameters"].get("batch_data")
        is not None
    ):
        raise ge_exceptions.InvalidConfigError(
            f'batch_data found in batch_request cannot be saved to CheckpointStore "{checkpoint_store_name}"'
        )

    checkpoint_config = filter_properties_dict(
        properties=checkpoint_config, clean_falsy=True
    )
    new_checkpoint: Union[
        Checkpoint, SimpleCheckpoint, LegacyCheckpoint
    ] = instantiate_class_from_config(
        config=checkpoint_config,
        runtime_environment={
            "data_context": data_context,
        },
        config_defaults={
            "module_name": "great_expectations.checkpoint.checkpoint",
        },
    )

    if ge_cloud_mode:
        key: GeCloudIdentifier = GeCloudIdentifier(
            resource_type="contract", ge_cloud_id=ge_cloud_id
        )
    else:
        key: ConfigurationIdentifier = ConfigurationIdentifier(
            configuration_key=name,
        )

    checkpoint_config = CheckpointConfig(**new_checkpoint.config.to_json_dict())
    checkpoint_ref = checkpoint_store.set(key=key, value=checkpoint_config)
    if isinstance(checkpoint_ref, GeCloudIdAwareRef):
        ge_cloud_id = checkpoint_ref.ge_cloud_id
        new_checkpoint.config.ge_cloud_id = uuid.UUID(ge_cloud_id)
    return new_checkpoint


def get_checkpoint(
    data_context: "DataContext",  # noqa: F821
    checkpoint_store: CheckpointStore,
    name: Optional[str] = None,
    ge_cloud_id: Optional[str] = None,
) -> Union[Checkpoint, LegacyCheckpoint]:
    if ge_cloud_id:
        key: GeCloudIdentifier = GeCloudIdentifier(
            resource_type="contract", ge_cloud_id=ge_cloud_id
        )
    else:
        key: ConfigurationIdentifier = ConfigurationIdentifier(
            configuration_key=name,
        )
    try:
        checkpoint_config: CheckpointConfig = checkpoint_store.get(key=key)
    except ge_exceptions.InvalidKeyError as exc_ik:
        raise ge_exceptions.CheckpointNotFoundError(
            message=f'Non-existent Checkpoint configuration named "{key.configuration_key}".\n\nDetails: {exc_ik}'
        )
    except ValidationError as exc_ve:
        raise ge_exceptions.InvalidCheckpointConfigError(
            message="Invalid Checkpoint configuration", validation_error=exc_ve
        )

    if checkpoint_config.config_version is None:
        if not (
            "batches" in checkpoint_config.to_json_dict()
            and (
                len(checkpoint_config.to_json_dict()["batches"]) == 0
                or {"batch_kwargs", "expectation_suite_names",}.issubset(
                    set(
                        list(
                            itertools.chain.from_iterable(
                                [
                                    item.keys()
                                    for item in checkpoint_config.to_json_dict()[
                                        "batches"
                                    ]
                                ]
                            )
                        )
                    )
                )
            )
        ):
            raise ge_exceptions.CheckpointError(
                message="Attempt to instantiate LegacyCheckpoint with insufficient and/or incorrect arguments."
            )

    config: dict = checkpoint_config.to_json_dict()
    if name:
        config.update({"name": name})
    config = filter_properties_dict(properties=config, clean_falsy=True)
    checkpoint: Union[Checkpoint, LegacyCheckpoint] = instantiate_class_from_config(
        config=config,
        runtime_environment={
            "data_context": data_context,
        },
        config_defaults={
            "module_name": "great_expectations.checkpoint",
        },
    )

    return checkpoint


def delete_checkpoint(
    checkpoint_store: CheckpointStore,
    name: Optional[str] = None,
    ge_cloud_id: Optional[str] = None,
):
    assert bool(name) ^ bool(ge_cloud_id), "Must provide either name or ge_cloud_id."

    if ge_cloud_id:
        key: GeCloudIdentifier = GeCloudIdentifier(
            resource_type="contract", ge_cloud_id=ge_cloud_id
        )
    else:
        key: ConfigurationIdentifier = ConfigurationIdentifier(configuration_key=name)

    try:
        checkpoint_store.remove_key(key=key)
    except ge_exceptions.InvalidKeyError as exc_ik:
        raise ge_exceptions.CheckpointNotFoundError(
            message=f'Non-existent Checkpoint configuration named "{key.configuration_key}".\n\nDetails: {exc_ik}'
        )


def run_checkpoint(
    data_context: "DataContext",  # noqa: F821
    checkpoint_store: CheckpointStore,
    ge_cloud_mode: bool,
    checkpoint_name: Optional[str] = None,
    template_name: Optional[str] = None,
    run_name_template: Optional[str] = None,
    expectation_suite_name: Optional[str] = None,
    batch_request: Optional[Union[BatchRequest, dict]] = None,
    action_list: Optional[List[dict]] = None,
    evaluation_parameters: Optional[dict] = None,
    runtime_configuration: Optional[dict] = None,
    validations: Optional[List[dict]] = None,
    profilers: Optional[List[dict]] = None,
    run_id: Optional[Union[str, int, float]] = None,
    run_name: Optional[str] = None,
    run_time: Optional[datetime.datetime] = None,
    result_format: Optional[str] = None,
    ge_cloud_id: Optional[str] = None,
    expectation_suite_ge_cloud_id: Optional[str] = None,
    **kwargs,
) -> CheckpointResult:
    """
    Validate against a pre-defined Checkpoint. (Experimental)
    Args:
        data_context: DataContext for Checkpoint class instantiation purposes
        checkpoint_store: CheckpointStore for managing Checkpoint configurations
        ge_cloud_mode: Whether or not Great Expectations is operating in the cloud mode
        checkpoint_name: The name of a Checkpoint defined via the CLI or by manually creating a yml file
        template_name: The name of a Checkpoint template to retrieve from the CheckpointStore
        run_name_template: The template to use for run_name
        expectation_suite_name: Expectation suite to be used by Checkpoint run
        batch_request: Batch request to be used by Checkpoint run
        action_list: List of actions to be performed by the Checkpoint
        evaluation_parameters: $parameter_name syntax references to be evaluated at runtime
        runtime_configuration: Runtime configuration override parameters
        validations: Validations to be performed by the Checkpoint run
        profilers: Profilers to be used by the Checkpoint run
        run_id: The run_id for the validation; if None, a default value will be used
        run_name: The run_name for the validation; if None, a default value will be used
        run_time: The date/time of the run
        result_format: One of several supported formatting directives for expectation validation results
        ge_cloud_id: Great Expectations Cloud id for the checkpoint
        expectation_suite_ge_cloud_id: Great Expectations Cloud id for the expectation suite
        **kwargs: Additional kwargs to pass to the validation operator

    Returns:
        CheckpointResult
    """
    # TODO mark experimental
    batch_request, validations = get_batch_request_dict(batch_request, validations)
    checkpoint: Union[Checkpoint, SimpleCheckpoint, LegacyCheckpoint] = get_checkpoint(
        data_context=data_context,
        checkpoint_store=checkpoint_store,
        name=checkpoint_name,
        ge_cloud_id=ge_cloud_id,
    )
    checkpoint_config_from_store: dict = checkpoint.config.to_json_dict()

    if (
        "runtime_configuration" in checkpoint_config_from_store
        and "result_format" in checkpoint_config_from_store["runtime_configuration"]
    ):
        result_format = result_format or checkpoint_config_from_store[
            "runtime_configuration"
        ].pop("result_format")

    if result_format is None:
        result_format = {"result_format": "SUMMARY"}

    checkpoint_config_from_call_args: dict = {
        "template_name": template_name,
        "run_name_template": run_name_template,
        "expectation_suite_name": expectation_suite_name,
        "batch_request": batch_request,
        "action_list": action_list,
        "evaluation_parameters": evaluation_parameters,
        "runtime_configuration": runtime_configuration,
        "validations": validations,
        "profilers": profilers,
        "run_id": run_id,
        "run_name": run_name,
        "run_time": run_time,
        "result_format": result_format,
        "expectation_suite_ge_cloud_id": expectation_suite_ge_cloud_id,
    }

    checkpoint_config: dict = {
        key: value
        for key, value in checkpoint_config_from_store.items()
        if key in checkpoint_config_from_call_args
    }
    checkpoint_config.update(checkpoint_config_from_call_args)
    if not ge_cloud_mode:
        batch_data_list = []
        batch_data = None
        if checkpoint_config.get("validations") is not None:
            for val in checkpoint_config["validations"]:
                if (
                    val.get("batch_request") is not None
                    and val["batch_request"].get("runtime_parameters") is not None
                    and val["batch_request"]["runtime_parameters"].get("batch_data")
                    is not None
                ):
                    batch_data_list.append(
                        val["batch_request"]["runtime_parameters"].pop("batch_data")
                    )
        elif (
            checkpoint_config.get("batch_request") is not None
            and checkpoint_config["batch_request"].get("runtime_parameters") is not None
            and checkpoint_config["batch_request"]["runtime_parameters"].get(
                "batch_data"
            )
            is not None
        ):
            batch_data = checkpoint_config["batch_request"]["runtime_parameters"].pop(
                "batch_data"
            )
        checkpoint_config = filter_properties_dict(
            properties=checkpoint_config, clean_falsy=True
        )
        if len(batch_data_list) > 0:
            for idx, val in enumerate(checkpoint_config.get("validations")):
                if batch_data_list[idx] is not None:
                    val["batch_request"]["runtime_parameters"][
                        "batch_data"
                    ] = batch_data_list[idx]
        elif batch_data is not None:
            checkpoint_config["batch_request"]["runtime_parameters"][
                "batch_data"
            ] = batch_data

    checkpoint_run_arguments: dict = dict(**checkpoint_config, **kwargs)

    return checkpoint.run(**checkpoint_run_arguments)


def default_checkpoints_exist(directory_path: str) -> bool:
    if not directory_path:
        return False

    checkpoints_directory_path: str = os.path.join(
        directory_path,
        DataContextConfigDefaults.DEFAULT_CHECKPOINT_STORE_BASE_DIRECTORY_RELATIVE_NAME.value,
    )
    return os.path.isdir(checkpoints_directory_path)
