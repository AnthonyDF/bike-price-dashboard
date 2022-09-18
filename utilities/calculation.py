def running_sum(df_daily_count, date):
  return df_daily_count[df_daily_count.scraped_date <= date].url.sum()