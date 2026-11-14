CREATE VIEW order_metrics AS
SELECT o.order_id, o.hub_id, h.hub_name, o.service_date, o.order_hour,
       CASE WHEN w.precipitation_mm IS NULL THEN 'Unknown'
            WHEN w.precipitation_mm >= 10 THEN 'Heavy rain'
            WHEN w.precipitation_mm >= 1 THEN 'Rain'
            ELSE 'Dry (<1 mm)' END AS rain_band,
       w.precipitation_mm,
       CASE WHEN o.order_hour IN (12, 13, 18, 19, 20) THEN 'Peak' ELSE 'Off-peak' END AS shift_band,
       s.scheduled_riders, o.promised_minutes,
       o.dispatch_minutes, o.pickup_minutes, o.travel_minutes,
       o.dispatch_minutes + o.pickup_minutes + o.travel_minutes AS total_minutes,
       CASE WHEN o.dispatch_minutes + o.pickup_minutes + o.travel_minutes > o.promised_minutes
            THEN 1 ELSE 0 END AS breached
FROM orders o
JOIN hubs h ON o.hub_id = h.hub_id
LEFT JOIN weather_daily w ON o.service_date = w.service_date
LEFT JOIN rider_slots s
    ON o.hub_id = s.hub_id AND o.service_date = s.service_date AND o.order_hour = s.order_hour;

CREATE VIEW slot_metrics AS
WITH counts AS (
    SELECT hub_id, service_date, order_hour, COUNT(*) AS orders, SUM(breached) AS breaches
    FROM order_metrics
    GROUP BY hub_id, service_date, order_hour
)
SELECT h.hub_name, s.service_date, s.order_hour, s.scheduled_riders,
       COALESCE(c.orders, 0) AS orders, COALESCE(c.breaches, 0) AS breaches,
       ROUND(1.0 * COALESCE(c.orders, 0) / s.scheduled_riders, 3) AS orders_per_rider,
       CASE WHEN c.orders >= 8 AND 1.0 * c.orders / s.scheduled_riders >= 3
                  AND 1.0 * c.breaches / c.orders >= 0.20
            THEN 1 ELSE 0 END AS staffing_review
FROM rider_slots s
JOIN hubs h ON s.hub_id = h.hub_id
LEFT JOIN counts c
    ON s.hub_id = c.hub_id AND s.service_date = c.service_date AND s.order_hour = c.order_hour;

CREATE VIEW rain_by_hub_and_shift AS
SELECT hub_name, shift_band, rain_band, COUNT(*) AS orders, SUM(breached) AS breaches,
       AVG(1.0 * breached) AS breach_rate,
       AVG(dispatch_minutes) AS dispatch_avg, AVG(pickup_minutes) AS pickup_avg,
       AVG(travel_minutes) AS travel_avg
FROM order_metrics
WHERE rain_band <> 'Unknown'
GROUP BY hub_name, shift_band, rain_band;
