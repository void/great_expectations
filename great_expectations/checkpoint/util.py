import copy
import datetime
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Union

import requests

import great_expectations.exceptions as ge_exceptions
from great_expectations.core.batch import BatchRequest, RuntimeBatchRequest
from great_expectations.core.util import nested_update
from great_expectations.data_context.types.base import CheckpointConfig
from great_expectations.util import filter_properties_dict

logger = logging.getLogger(__name__)


def send_slack_notification(
    query, slack_webhook=None, slack_channel=None, slack_token=None
):
    session = requests.Session()
    url = slack_webhook
    query = query
    headers = None

    if not slack_webhook:
        url = "https://slack.com/api/chat.postMessage"
        headers = {"Authorization": f"Bearer {slack_token}"}
        query["channel"] = slack_channel

    try:
        response = session.post(url=url, headers=headers, json=query)
    except requests.ConnectionError:
        logger.warning(
            "Failed to connect to Slack webhook at {url} "
            "after {max_retries} retries.".format(url=slack_webhook, max_retries=10)
        )
    except Exception as e:
        logger.error(str(e))
    else:
        if response.status_code != 200:
            logger.warning(
                "Request to Slack webhook at {url} "
                "returned error {status_code}: {text}".format(
                    url=slack_webhook,
                    status_code=response.status_code,
                    text=response.text,
                )
            )

        else:
            return "Slack notification succeeded."


# noinspection SpellCheckingInspection
def send_opsgenie_alert(query, suite_name, settings):
    """Creates an alert in Opsgenie."""
    if settings["region"] is not None:
        url = "https://api.{region}.opsgenie.com/v2/alerts".format(
            region=settings["region"]
        )  # accommodate for Europeans
    else:
        url = "https://api.opsgenie.com/v2/alerts"

    headers = {
        "Authorization": "GenieKey {api_key}".format(api_key=settings["api_key"])
    }
    payload = {
        "message": "Great Expectations suite {suite_name} failed".format(
            suite_name=suite_name
        ),
        "description": query,
        "priority": settings["priority"],  # allow this to be modified in settings
    }

    session = requests.Session()

    try:
        response = session.post(url, headers=headers, json=payload)
    except requests.ConnectionError:
        logger.warning("Failed to connect to Opsgenie")
    except Exception as e:
        logger.error(str(e))
    else:
        if response.status_code != 202:
            logger.warning(
                "Request to Opsgenie API at {url} "
                "returned error {status_code}: {text}".format(
                    url=url,
                    status_code=response.status_code,
                    text=response.text,
                )
            )
        else:
            return "success"
    return "error"


def send_microsoft_teams_notifications(query, microsoft_teams_webhook):
    session = requests.Session()
    try:
        response = session.post(url=microsoft_teams_webhook, json=query)
    except requests.ConnectionError:
        logger.warning(
            "Failed to connect to Microsoft Teams webhook at {url} "
            "after {max_retries} retries.".format(
                url=microsoft_teams_webhook, max_retries=10
            )
        )
    except Exception as e:
        logger.error(str(e))
    else:
        if response.status_code != 200:
            logger.warning(
                "Request to Microsoft Teams webhook at {url} "
                "returned error {status_code}: {text}".format(
                    url=microsoft_teams_webhook,
                    status_code=response.status_code,
                    text=response.text,
                )
            )
            return
        else:
            return "Microsoft Teams notification succeeded."


def send_webhook_notifications(query, webhook, target_platform):
    session = requests.Session()
    try:
        response = session.post(url=webhook, json=query)
    except requests.ConnectionError:
        logger.warning(
            "Failed to connect to {target_platform} webhook at {url} "
            "after {max_retries} retries.".format(
                url=webhook,
                max_retries=10,
                target_platform=target_platform,
            )
        )
    except Exception as e:
        logger.error(str(e))
    else:
        if response.status_code != 200:
            logger.warning(
                "Request to {target_platform} webhook at {url} "
                "returned error {status_code}: {text}".format(
                    url=webhook,
                    status_code=response.status_code,
                    target_platform=target_platform,
                    text=response.text,
                )
            )
        else:
            return "{target_platform} notification succeeded.".format(
                target_platform=target_platform
            )


# noinspection SpellCheckingInspection
def send_email(
    title,
    html,
    smtp_address,
    smtp_port,
    sender_login,
    sender_password,
    sender_alias,
    receiver_emails_list,
    use_tls,
    use_ssl,
):
    msg = MIMEMultipart()
    msg["From"] = sender_alias
    msg["To"] = ", ".join(receiver_emails_list)
    msg["Subject"] = title
    msg.attach(MIMEText(html, "html"))
    try:
        if use_ssl:
            if use_tls:
                logger.warning("Please choose between SSL or TLS, will default to SSL")
            context = ssl.create_default_context()
            mailserver = smtplib.SMTP_SSL(smtp_address, smtp_port, context=context)
        elif use_tls:
            mailserver = smtplib.SMTP(smtp_address, smtp_port)
            context = ssl.create_default_context()
            mailserver.starttls(context=context)
        else:
            logger.warning("Not using TLS or SSL to send an email is not secure")
            mailserver = smtplib.SMTP(smtp_address, smtp_port)
        mailserver.login(sender_login, sender_password)
        mailserver.sendmail(sender_alias, receiver_emails_list, msg.as_string())
        mailserver.quit()
    except smtplib.SMTPConnectError:
        logger.error(f"Failed to connect to the SMTP server at address: {smtp_address}")
    except smtplib.SMTPAuthenticationError:
        logger.error(
            f"Failed to authenticate to the SMTP server at address: {smtp_address}"
        )
    except Exception as e:
        logger.error(str(e))
    else:
        return "success"


# TODO: <Alex>A common utility function should be factored out from DataContext.get_batch_list() for any purpose.</Alex>
def get_runtime_batch_request(
    substituted_runtime_config: CheckpointConfig,
    validation_batch_request: Optional[Union[dict, BatchRequest]] = None,
    ge_cloud_mode: bool = False,
) -> Optional[BatchRequest]:
    runtime_config_batch_request = substituted_runtime_config.batch_request

    if runtime_config_batch_request is None and validation_batch_request is None:
        return None

    if runtime_config_batch_request is None:
        runtime_config_batch_request = {}

    if validation_batch_request is None:
        validation_batch_request = {}

    if isinstance(validation_batch_request, BatchRequest):
        validation_batch_request = validation_batch_request.to_dict()

    if isinstance(runtime_config_batch_request, BatchRequest):
        runtime_config_batch_request = runtime_config_batch_request.to_dict()

    effective_batch_request: dict = dict(
        **runtime_config_batch_request, **validation_batch_request
    )

    batch_request_class: type

    if "runtime_parameters" in effective_batch_request:
        batch_request_class = RuntimeBatchRequest
    else:
        batch_request_class = BatchRequest

    if (
        validation_batch_request.get("runtime_parameters") is not None
        and validation_batch_request["runtime_parameters"].get("batch_data") is not None
    ):
        batch_data = validation_batch_request["runtime_parameters"].pop("batch_data")
        runtime_batch_request_dict: dict = copy.deepcopy(validation_batch_request)
        validation_batch_request["runtime_parameters"][
            "batch_data"
        ] = runtime_batch_request_dict["runtime_parameters"]["batch_data"] = batch_data
    else:
        runtime_batch_request_dict: dict = copy.deepcopy(validation_batch_request)

    for key, runtime_batch_request_dict_val in runtime_batch_request_dict.items():
        runtime_config_batch_request_val = runtime_config_batch_request.get(key)
        if (
            runtime_batch_request_dict_val is not None
            and runtime_config_batch_request_val is not None
        ):
            raise ge_exceptions.CheckpointError(
                f'BatchRequest attribute "{key}" was specified in both validation and top-level CheckpointConfig.'
            )
    runtime_batch_request_dict.update(runtime_config_batch_request)

    if ge_cloud_mode and batch_request_class is RuntimeBatchRequest:
        batch_identifiers = runtime_batch_request_dict.get("batch_identifiers", {})
        if len(batch_identifiers.keys()) == 0:
            batch_identifiers["timestamp"] = str(datetime.datetime.now())
            runtime_batch_request_dict["batch_identifiers"] = batch_identifiers

    filter_properties_dict(
        properties=runtime_batch_request_dict,
        keep_fields=batch_request_class.field_names,
        clean_nulls=False,
        inplace=True,
    )

    return batch_request_class(**runtime_batch_request_dict)


def get_substituted_validation_dict(
    substituted_runtime_config: CheckpointConfig, validation_dict: dict
) -> dict:
    substituted_validation_dict = {
        "batch_request": get_runtime_batch_request(
            substituted_runtime_config=substituted_runtime_config,
            validation_batch_request=validation_dict.get("batch_request"),
        ),
        "expectation_suite_name": validation_dict.get("expectation_suite_name")
        or substituted_runtime_config.expectation_suite_name,
        "expectation_suite_ge_cloud_id": validation_dict.get(
            "expectation_suite_ge_cloud_id"
        )
        or substituted_runtime_config.expectation_suite_ge_cloud_id,
        "action_list": CheckpointConfig.get_updated_action_list(
            base_action_list=substituted_runtime_config.action_list,
            other_action_list=validation_dict.get("action_list", {}),
        ),
        "evaluation_parameters": nested_update(
            substituted_runtime_config.evaluation_parameters,
            validation_dict.get("evaluation_parameters", {}),
        ),
        "runtime_configuration": nested_update(
            substituted_runtime_config.runtime_configuration,
            validation_dict.get("runtime_configuration", {}),
        ),
    }
    if validation_dict.get("name") is not None:
        substituted_validation_dict["name"] = validation_dict["name"]
    validate_validation_dict(substituted_validation_dict)
    return substituted_validation_dict


def validate_validation_dict(validation_dict: dict):
    if validation_dict.get("batch_request") is None:
        raise ge_exceptions.CheckpointError("validation batch_request cannot be None")
    if not validation_dict.get("expectation_suite_name"):
        raise ge_exceptions.CheckpointError(
            "validation expectation_suite_name must be specified"
        )
    if not validation_dict.get("action_list"):
        raise ge_exceptions.CheckpointError("validation action_list cannot be empty")
