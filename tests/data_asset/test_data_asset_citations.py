from great_expectations.util import filter_properties_dict


def test_data_asset_citations(pandas_dataset):
    citation_date = "2020-02-27T12:34:56.123456Z"
    pandas_dataset.add_citation("test citation", citation_date=citation_date)
    suite = pandas_dataset.get_expectation_suite()
    assert filter_properties_dict(
        properties=suite.meta["citations"][0],
        delete_fields={
            "interactive",
        },
        clean_falsy=True,
    ) == filter_properties_dict(
        properties={
            "comment": "test citation",
            "batch_kwargs": pandas_dataset.batch_kwargs,
            "batch_parameters": pandas_dataset.batch_parameters,
            "batch_markers": pandas_dataset.batch_markers,
            "citation_date": citation_date,
        },
        clean_falsy=True,
    )
