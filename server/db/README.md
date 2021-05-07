# TheOrgBook Database(s)

## Overview

TheOrgBook DB is used to store the core Organizational data for searching (notably names, locations/addresses and claims held) and the claims themselves.

## Development

The DB component is an instance of Postgres. The schema and data loading is all handled by TheOrgBook API, and the Postgres image being used is a Red Hat image. As such, there is no build or database initialization associated with the DB - just the Deployment.

# Database Schema Documentation

Databases are documented using [SchemaSpy](https://github.com/bcgov/SchemaSpy).

# Adding Business Numbers in the Name table

The following SQL command will copy Business Nunbers from the `Attribute` table and insert them into the `Name` table if they don't exist already:

```SQL
INSERT INTO public.name(create_timestamp, update_timestamp, text, credential_id, type)
SELECT  att.create_timestamp, NOW(), att.value, att.credential_id, att.type
FROM public.attribute att
WHERE type = 'business_number' AND NOT EXISTS (SELECT 1 FROM name n WHERE n.type = 'business_number' AND n.credential_id = att.credential_id);
```