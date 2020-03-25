# Search Index Integration

Full text search is supported using a combination of SOLR with Haystack to support integration with Django.

The most recent PR that updated the search index is here:  https://github.com/hyperledger/aries-vcr/pull/425.  This added
a new attribute to the search index, and is a useful guide to how the search index works.

## Specifying the Search Index

The index is specified with this file:  https://github.com/hyperledger/aries-vcr/blob/master/server/vcr-server/api/v2/search_indexes.py -  This maps the model attributes that Haystack/Solr will index, and must match the Solr index file:  https://github.com/hyperledger/aries-vcr/blob/master/server/solr/cores/credential_registry/conf/schema.xml

## Mapping Related Objects

The primary object that is indexed is the Credential, however the index must be updated on updates to related tables.  This is handled by integrating with Django/Haystack signals, in the following file:  https://github.com/hyperledger/aries-vcr/blob/master/server/vcr-server/api/v2/signals.py -  Note that model objects that trigger search index updates must have the `reindex_related` attribute defined, for example:

https://github.com/hyperledger/aries-vcr/blob/master/server/vcr-server/api/v2/models/CredentialSet.py#L8

... and ...

https://github.com/hyperledger/aries-vcr/blob/master/server/vcr-server/api/v2/models/Topic.py#L12

