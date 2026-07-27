-- Qwant FR user-query sample — generates qwant_fr_queries_sample_20260724.csv
-- Source: prod_amplify.event_silver.ad_request (runs in the Databricks SQL editor, any warehouse with prod_amplify read)
-- Sample: 1,000 random DISTINCT search terms + 7-day frequency, Qwant AI (publisher 1276), geo FR.
-- Notes:
--   * uniform over distinct queries (not traffic-weighted): ORDER BY freq DESC instead for head queries
--   * publisher ids from prod_amplify.ssp.publisher: 1107 = "Qwant", 1276 = "Qwant AI"
--   * these are SERP-era search terms; conversation payloads (intent column) start with 3.0 ghost endpoints

SELECT usr_search_term AS query, count(*) AS freq_7d
FROM prod_amplify.event_silver.ad_request
WHERE pub_publisher_id = 1276
  AND usr_geo_country_code = 'FR'
  AND amp_ad_request_date >= current_date() - INTERVAL 7 DAYS
  AND usr_search_term IS NOT NULL
  AND length(trim(usr_search_term)) > 1
GROUP BY 1
ORDER BY rand()
LIMIT 1000;
