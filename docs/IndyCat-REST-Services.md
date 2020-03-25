# Aries VCR Credential Registry REST Services

The Credential Registry provides a [Swagger](https://swagger.io/) ([OpenAPI](https://www.openapis.org)) page that provides an interactive way to test out its available APIs.  The Credential Registry's Swagger page is available in a local Aries VCR install at [http://localhost:8080/api/](http://localhost:8080/api/), or (for example) in a stable test deployment at [https://test.orgbook.gov.bc.ca/api/](https://test.orgbook.gov.bc.ca/api/).

## Organization Name Search

The main API for performing an organization name search is `GET /v2/search/autocomplete` on the Swagger page.  You can also just run the search from your browser against your local OrgBook instance by going to:

```
http://localhost:8080/api/v2/search/autocomplete?category=<text to search>
```

This endpoint returns a list of registered organizations names matching the supplied search criteria.  The search is based on SOLR indexing and will return a list of organizations based on a closest match algorithm. If there is an organization name with an exact match to the search category, it will always be first in the response list.  For example:

```
http://localhost:8080/api/v2/search/autocomplete?category="MY COMPANY CORP"
```

Note that search paging parameters (page size and initial index) can be specified using additional REST API parameters. That is evident on the Swagger page entry for that call.

The request returns the named organization (exact match, if any), as well as close matches to the name.  Data in the returned JSON structure (below) can then be used to query for additional information about the company.

``` jsonc
{
    "total": 10,
    "first_index": 1,
    "last_index": 10,
    "results": [
        {
            "id": 99,
            "names": [
                {
                    "id": 99,
                    "text": "MY COMPANY CORP.",
                    "language": null,
                    "credential_id": 99,
                    "type": "entity_name"
                }
            ],
            "inactive": false
        },
        {
        ...
        }
    ]
}
```

The `GET /v2/search/autocomplete` API endpoint is useful for populating an "autocomplete" search drop-down, like the one on the OrgBook home page ([https://orgbook.gov.bc.ca](https://orgbook.gov.bc.ca)).

You can get a more detailed set of data using the "facets" (`GET /v2/search/credential/topic/facets`) version of the search. For example,

```
http://localhost:8080/api/v2/search/credential/topic/facets?name=<text to search>
```

Review the returned JSON structure (below - abbreviated for clarity). A useful field for further searches is the "topic" ... "source_id"field, which is the BC Company number from BC Registries.

``` jsonc
"objects": {
    ...
    "results": [
        {
            ...
            "credential_set": {
                ...
            },
            "credential_type": {
                ...
            },
            "attributes": [
                ...
            ],
            "names": [
                ...
            ],
            "topic": {
                ...
                "source_id": "S0030754",
                ...
            },
            "related_topics": []
        }
    ]
}
```

You can use the `source_id` value in, for example, the following query to get more information about the organization.

```
http://test.orgbook.gov.bc.ca/api/v2/topic/ident/registration/S0030754/formatted
```

That provides some basic information about querying for organizations and then getting details on those organization. We recommend you experiment with other API endpoints using the Swagger pages on your local or the test instance.

