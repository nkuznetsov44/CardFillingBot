alter table budget add column start_date date not null default '2025-01-01';
alter table budget add column end_date date null;

alter table budget add constraint chk_budget_exactly_one_limit
check (
    (monthly_limit IS NOT NULL AND quarter_limit IS NULL AND year_limit IS NULL) OR
    (monthly_limit IS NULL AND quarter_limit IS NOT NULL AND year_limit IS NULL) OR
    (monthly_limit IS NULL AND quarter_limit IS NULL AND year_limit IS NOT NULL)
);

alter table budget add constraint chk_budget_monthly_dates
check (
    monthly_limit IS NULL OR (
        DAY(start_date) = 1 AND
        (end_date IS NULL OR (DAY(LAST_DAY(end_date)) = DAY(end_date)))
    )
);

alter table budget add constraint chk_budget_quarter_dates
check (
    quarter_limit IS NULL OR (
        DAY(start_date) = 1 AND
        MONTH(start_date) IN (1, 4, 7, 10) AND
        (end_date IS NULL OR (
            DAY(LAST_DAY(end_date)) = DAY(end_date) AND
            MONTH(end_date) IN (3, 6, 9, 12)
        ))
    )
);

alter table budget add constraint chk_budget_year_dates
check (
    year_limit IS NULL OR (
        DAYOFYEAR(start_date) = 1 AND
        (end_date IS NULL OR (MONTH(end_date) = 12 AND DAY(end_date) = 31))
    )
);
