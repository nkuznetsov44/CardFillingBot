CREATE OR REPLACE VIEW v_month_category_report AS
WITH RECURSIVE
bounds AS (
    SELECT
        CAST(DATE_FORMAT(MIN(cf.fill_date), '%Y-%m-01') AS DATE) AS start_month,
        CAST(DATE_FORMAT(MAX(cf.fill_date), '%Y-%m-01') AS DATE) AS end_month
    FROM card_fill cf
    WHERE cf.fill_scope IN (1,2,4)
),
months AS (
    SELECT start_month AS month_start, end_month
    FROM bounds
    WHERE start_month IS NOT NULL AND end_month IS NOT NULL

    UNION ALL

    SELECT DATE_ADD(month_start, INTERVAL 1 MONTH), end_month
    FROM months
    WHERE month_start < end_month
),
spend AS (
    SELECT
        CAST(DATE_FORMAT(cf.fill_date, '%Y-%m-01') AS DATE) AS month_start,
        cf.category_code,
        SUM(cf.amount) AS spend_amount
    FROM card_fill cf
    WHERE cf.fill_scope IN (1,2,4)
    GROUP BY
        CAST(DATE_FORMAT(cf.fill_date, '%Y-%m-01') AS DATE),
        cf.category_code
),
budgets_with_months AS (
    SELECT
        m.month_start,
        b.category_code,
        COALESCE(
            b.monthly_limit,
            b.quarter_limit / 3,
            b.year_limit / 12
        ) AS monthly_budget
    FROM months m
    CROSS JOIN budget b
    WHERE b.fill_scope = 1
      AND b.start_date <= LAST_DAY(m.month_start)
      AND (b.end_date IS NULL OR b.end_date >= m.month_start)
)
SELECT
    YEAR(m.month_start) AS year,
    CAST(m.month_start AS DATETIME) AS month,
    c.code AS category_code,
    c.name AS category_name,
    bg.monthly_budget AS monthly_budget,
    COALESCE(s.spend_amount, 0) AS spend_amount,
    SUM(COALESCE(s.spend_amount, 0)) OVER (
        PARTITION BY c.code, YEAR(m.month_start)
        ORDER BY m.month_start
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_spend
FROM months m
CROSS JOIN category c
LEFT JOIN budgets_with_months bg
       ON bg.month_start = m.month_start
      AND bg.category_code = c.code
LEFT JOIN spend s
       ON s.month_start = m.month_start
      AND s.category_code = c.code;

-------------------------------------------------------------

CREATE OR REPLACE VIEW v_income_vs_spend AS
WITH RECURSIVE
bounds AS (
    SELECT
        CAST(DATE_FORMAT(MIN(d.dt), '%Y-%m-01') AS DATE) AS start_month,
        CAST(DATE_FORMAT(MAX(d.dt), '%Y-%m-01') AS DATE) AS end_month
    FROM (
        SELECT cf.fill_date AS dt
        FROM card_fill cf
        WHERE cf.fill_scope IN (1,2,4)

        UNION ALL

        SELECT i.income_date AS dt
        FROM income i
        WHERE i.fill_scope IN (1,2,4)
    ) d
),
months AS (
    SELECT start_month AS month_start, end_month
    FROM bounds
    WHERE start_month IS NOT NULL AND end_month IS NOT NULL

    UNION ALL

    SELECT DATE_ADD(month_start, INTERVAL 1 MONTH), end_month
    FROM months
    WHERE month_start < end_month
),
spend_m AS (
    SELECT
        CAST(DATE_FORMAT(cf.fill_date, '%Y-%m-01') AS DATE) AS month_start,
        SUM(cf.amount) AS spend_amount
    FROM card_fill cf
    WHERE cf.fill_scope IN (1,2,4)
    GROUP BY CAST(DATE_FORMAT(cf.fill_date, '%Y-%m-01') AS DATE)
),
income_m AS (
    SELECT
        CAST(DATE_FORMAT(i.income_date, '%Y-%m-01') AS DATE) AS month_start,
        SUM(i.amount) AS income_amount
    FROM income i
    WHERE i.fill_scope IN (1,2,4)
    GROUP BY CAST(DATE_FORMAT(i.income_date, '%Y-%m-01') AS DATE)
)
SELECT
    YEAR(m.month_start) AS year,
    CAST(m.month_start AS DATETIME) AS month,
    COALESCE(sm.spend_amount, 0) AS spend_amount,
    COALESCE(im.income_amount, 0) AS income_amount,
    SUM(COALESCE(sm.spend_amount, 0)) OVER (
        PARTITION BY YEAR(m.month_start)
        ORDER BY m.month_start
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_spend,
    SUM(COALESCE(im.income_amount, 0)) OVER (
        PARTITION BY YEAR(m.month_start)
        ORDER BY m.month_start
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_income
FROM months m
LEFT JOIN spend_m sm
       ON sm.month_start = m.month_start
LEFT JOIN income_m im
       ON im.month_start = m.month_start;
