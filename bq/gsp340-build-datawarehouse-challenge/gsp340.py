# -*- coding: utf-8 -*-
"""Qwiklabs GSP340 Build and optimize datawarehouse in BigQuery challenge

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/github/bobbae/gcp/blob/main/bq/gsp340-build-datawarehouse-challenge/gsp340.ipynb

# Before you begin


1.   Use the [Cloud Resource Manager](https://console.cloud.google.com/cloud-resource-manager) to Create a Cloud Platform project if you do not already have one.
2.   [Enable billing](https://support.google.com/cloud/answer/6293499#enable-billing) for the project.
3.   [Enable BigQuery](https://console.cloud.google.com/flows/enableapi?apiid=bigquery) APIs for the project.

### Provide your credentials to the runtime
"""

# If running from cloud-shell, DEVSHELL_PROJECT_ID environment variable may contain project ID.
# import os
# project_id = os.getenv("DEVSHELL_PROJECT_ID")

# Otherwise, set project_id manually
# project_id = 'XXXyourprojectID'

from google.colab import auth
auth.authenticate_user()
print('Authenticated')

project_id = 'XXX-your-project-id'

"""# GSP 340
https://www.qwiklabs.com/focuses/14341?locale=zh_TW&parent=catalog

### Create dataset
"""

from google.cloud import bigquery
import pandas as pd

client = bigquery.Client(project=project_id)
dataset_id = 'covid'
dataset = client.create_dataset(dataset_id)
dataset.location = 'US'

"""### Task 1: Create a table partitioned by date"""

from google.colab import syntax
import pandas as pd

query = syntax.sql('''
CREATE TABLE covid.oxford
PARTITION BY date
OPTIONS (partition_expiration_days=90)
AS SELECT * FROM `bigquery-public-data.covid19_govt_response.oxford_policy_tracker`
WHERE alpha_3_code NOT IN ('BGR', 'USA')
''')
pd.io.gbq.read_gbq(query, project_id=project_id, dialect='standard')

"""### Task2: Add new columns to your table"""

query = syntax.sql('''
ALTER TABLE covid.oxford
ADD COLUMN IF NOT EXISTS population INT64,
ADD COLUMN IF NOT EXISTS country_area FLOAT64,
ADD COLUMN IF NOT EXISTS mobility STRUCT<
avg_retail FLOAT64,
avg_grocery FLOAT64,
avg_parks FLOAT64,
avg_transit FLOAT64,
avg_workplace FLOAT64,
avg_residential FLOAT64
>
''')
pd.io.gbq.read_gbq(query, project_id=project_id, dialect='standard')

"""### Task3: Add country population data to the population column"""

query = syntax.sql('''
UPDATE `covid.oxford` t0
SET t0.population = t1.pop_data_2019
FROM `bigquery-public-data.covid19_ecdc.covid_19_geographic_distribution_worldwide` t1
WHERE t0.date = t1.date AND t0.alpha_3_code=t1.country_territory_code
''')
pd.io.gbq.read_gbq(query, project_id=project_id, dialect='standard')

"""### Task4: Add country area data to the country_area column"""

query = syntax.sql('''
UPDATE `covid.oxford` t0
SET t0.country_area = t1.country_area
FROM `bigquery-public-data.census_bureau_international.country_names_area` t1
WHERE t0.country_name = t1.country_name
''')
pd.io.gbq.read_gbq(query, project_id=project_id, dialect='standard')

"""### Task5: Populate the mobility record data"""

query = syntax.sql('''
UPDATE `covid.oxford` t0
SET t0.mobility = STRUCT<
avg_retail FLOAT64, avg_grocery FLOAT64, avg_parks FLOAT64, avg_transit FLOAT64,
avg_workplace FLOAT64, avg_residential FLOAT64
>
(t1.avg_retail, t1.avg_grocery, t1.avg_parks, t1.avg_transit,
t1.avg_workplace, t1.avg_residential)
FROM ( SELECT country_region, date,
  AVG(retail_and_recreation_percent_change_from_baseline) as avg_retail,
  AVG(grocery_and_pharmacy_percent_change_from_baseline) as avg_grocery,
  AVG(parks_percent_change_from_baseline) as avg_parks,
  AVG(transit_stations_percent_change_from_baseline) as avg_transit,
  AVG(workplaces_percent_change_from_baseline) as avg_workplace,
  AVG(residential_percent_change_from_baseline) as avg_residential
  FROM `bigquery-public-data.covid19_google_mobility.mobility_report`
  GROUP BY country_region, date) AS t1
WHERE t0.date = t1.date AND t0.country_name=t1.country_region
''')
pd.io.gbq.read_gbq(query, project_id=project_id, dialect='standard')

"""### Task6: Query missing data in population and country_area columns"""

query = syntax.sql('''
SELECT DISTINCT country_name
FROM `covid.oxford`
WHERE population IS NULL
UNION ALL
SELECT DISTINCT country_name
FROM `covid.oxford`
WHERE country_area IS NULL
ORDER BY country_name ASC
''')
pd.io.gbq.read_gbq(query, project_id=project_id, dialect='standard')