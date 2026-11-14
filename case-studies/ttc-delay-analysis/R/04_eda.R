# Descriptive analysis and figures. All aggregation is done in the SQL views;
# this script only reads them and plots the results.

source("R/00_config.R")

con <- connect_db()
on.exit(DBI::dbDisconnect(con), add = TRUE)

q <- function(sql) DBI::dbGetQuery(con, sql)
mode_colours <- c(subway = "#B3282D", streetcar = "#2F6F73", bus = "#C58B2A")

mode_summary <- q("
    select mode,
           count(*) as incidents,
           sum(delay_minutes) as delay_minutes,
           round(avg(delay_minutes), 2) as avg_delay_minutes,
           percentile_cont(0.5) within group (order by delay_minutes) as median_delay_minutes,
           count(*) filter (where major_delay) as major_incidents,
           round(100.0 * count(*) filter (where major_delay) / count(*), 2) as major_delay_rate_pct
    from analytics.stg_delays
    group by mode
    order by incidents desc
")
write_table(mode_summary, "eda_mode_summary.csv")

line_summary <- q("
    select mode, line, incidents, major_incidents, delay_minutes,
           avg_delay_minutes, median_delay_minutes, p90_delay_minutes,
           pct_of_mode_delay_minutes, delay_rank_in_mode,
           cumulative_pct_of_mode
    from analytics.v_line_delay
    order by mode, delay_rank_in_mode
")
write_table(line_summary, "eda_line_summary.csv")

cause_summary <- q("
    select mode, cause_category, incidents, major_incidents, delay_minutes,
           avg_delay_minutes, pct_of_mode_incidents,
           pct_of_mode_delay_minutes, major_delay_rate_pct
    from analytics.v_cause_category
    order by mode, delay_minutes desc
")
write_table(cause_summary, "eda_cause_summary.csv")

hour_weekday <- q("
    select mode, weekday, hour, incidents, major_incidents, delay_minutes,
           major_delay_rate_pct
    from analytics.v_hour_weekday
    order by mode, weekday, hour
") |>
  dplyr::mutate(
    weekday = factor(weekday, levels = c(
      "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
      "Saturday", "Sunday"
    ))
  )
write_table(hour_weekday, "eda_hour_weekday.csv")

monthly <- q("
    select mode, year, month, month_start, incidents, major_incidents,
           delay_minutes, delay_minutes_same_month_previous_year,
           yoy_change_pct
    from analytics.v_monthly_mode
    order by mode, year, month
")
write_table(monthly, "eda_monthly_mode.csv")

daily <- q("
    select mode, delay_date, incidents, major_incidents, delay_minutes,
           incidents_28d_avg, delay_minutes_28d_sum, pct_of_day_all_modes
    from analytics.v_daily_mode
    order by mode, delay_date
")

delay_hist <- q("
    select mode, least(floor(delay_minutes / 5.0) * 5, 120) as delay_bin,
           count(*) as incidents
    from analytics.stg_delays
    group by mode, delay_bin
    order by mode, delay_bin
")

peak_hours <- hour_weekday |>
  dplyr::group_by(mode, hour) |>
  dplyr::summarise(
    incidents = sum(incidents),
    major_incidents = sum(major_incidents),
    major_delay_rate_pct = round(100 * major_incidents / incidents, 2),
    .groups = "drop"
  ) |>
  dplyr::arrange(mode, dplyr::desc(incidents)) |>
  dplyr::group_by(mode) |>
  dplyr::slice_head(n = 5) |>
  dplyr::ungroup()
write_table(peak_hours, "eda_peak_hours.csv")

# Figure 1: daily volume with a 28-day rolling average -----------------------
p1 <- ggplot(daily, aes(x = delay_date, y = incidents_28d_avg,
                        colour = mode)) +
  annotate("rect", xmin = COVID_START, xmax = COVID_END, ymin = -Inf,
           ymax = Inf, fill = "grey85", alpha = 0.5) +
  geom_line(linewidth = 0.8) +
  geom_vline(xintercept = as.numeric(COVID_START), linetype = "dashed",
             colour = "grey45") +
  annotate("text", x = COVID_START, y = Inf, label = "COVID period",
           hjust = -0.05, vjust = 1.4, size = 3.2, colour = "grey35") +
  scale_colour_manual(values = mode_colours) +
  scale_y_continuous(labels = scales::comma) +
  labs(
    title = "Reported TTC delays per day, 28-day rolling average",
    subtitle = "All reported incidents, by mode. Shaded band is 2020-03-15 to 2022-12-31.",
    x = NULL, y = "Incidents per day", colour = NULL,
    caption = "Source: City of Toronto TTC delay data. Last date in extract: 2026-09-30."
  ) +
  theme_ttc()
save_figure(p1, "fig01_daily_incidents_28d.png", width = 10, height = 5.5)

# Figure 2: major-delay rate heatmap ---------------------------------------
p2 <- ggplot(hour_weekday, aes(x = hour, y = weekday,
                               fill = major_delay_rate_pct)) +
  geom_tile(width = 0.95, height = 0.95) +
  facet_wrap(~ mode, ncol = 1) +
  scale_fill_gradientn(
    colours = c("#F4F1E8", "#E3B23C", "#B3282D"),
    labels = function(x) paste0(x, "%")
  ) +
  scale_x_continuous(breaks = seq(0, 23, 3)) +
  labs(
    title = "Share of incidents lasting 15 minutes or more",
    subtitle = "Hour of day by weekday, each mode on its own scale.",
    x = "Hour of day", y = NULL, fill = "Major-delay rate",
    caption = "Source: City of Toronto TTC delay data, 2014-2026."
  ) +
  theme_ttc() +
  theme(panel.grid = element_blank())
save_figure(p2, "fig02_major_delay_heatmap.png", width = 9, height = 8)

# Figure 3: top lines by delay minutes -------------------------------------
top_lines <- line_summary |>
  dplyr::filter(delay_rank_in_mode <= 8) |>
  dplyr::mutate(line_label = paste0(mode, " ", line))

p3 <- ggplot(top_lines, aes(x = delay_minutes / 1e6,
                            y = forcats::fct_reorder(line_label, delay_minutes),
                            fill = mode)) +
  geom_col(width = 0.72) +
  geom_text(aes(label = paste0(pct_of_mode_delay_minutes, "%")),
            hjust = -0.08, size = 3.1, colour = "grey25") +
  facet_wrap(~ mode, scales = "free_y", ncol = 1) +
  scale_fill_manual(values = mode_colours, guide = "none") +
  scale_x_continuous(labels = function(x) paste0(x, "M"),
                     expand = expansion(mult = c(0, 0.18))) +
  labs(
    title = "Top lines by cumulative reported delay minutes",
    subtitle = "Labels show each line's share of its own mode's delay minutes.",
    x = "Delay minutes (millions)", y = NULL,
    caption = "Lines with fewer than 100 incidents are excluded from rankings."
  ) +
  theme_ttc() +
  theme(axis.text.y = element_text(size = 8))
save_figure(p3, "fig03_top_lines.png", width = 9, height = 8)

# Figure 4: cause mix -------------------------------------------------------
p4 <- ggplot(cause_summary,
             aes(x = forcats::fct_reorder(cause_category,
                                          pct_of_mode_delay_minutes),
                 y = pct_of_mode_delay_minutes, fill = mode)) +
  geom_col(position = position_dodge(width = 0.82), width = 0.78) +
  coord_flip() +
  scale_fill_manual(values = mode_colours) +
  scale_y_continuous(labels = function(x) paste0(x, "%")) +
  labs(
    title = "Cause categories as a share of reported delay minutes",
    subtitle = "Bus and streetcar use coarse legacy categories before 2021; the 2025 extract uses TTC delay codes.",
    x = NULL, y = "Share of mode delay minutes", fill = NULL,
    caption = "Source: City of Toronto TTC delay data, 2014-2026."
  ) +
  theme_ttc()
save_figure(p4, "fig04_cause_mix.png", width = 9, height = 5)

# Figure 5: delay distribution ---------------------------------------------
p5 <- ggplot(delay_hist, aes(x = delay_bin, y = incidents, fill = mode)) +
  geom_col(width = 4.2) +
  facet_wrap(~ mode, scales = "free_y", ncol = 3) +
  scale_fill_manual(values = mode_colours, guide = "none") +
  scale_y_continuous(labels = scales::comma) +
  scale_x_continuous(breaks = seq(0, 120, 30),
                     labels = c("0", "30", "60", "90", "120+")) +
  labs(
    title = "Distribution of reported delay minutes",
    subtitle = "Five-minute bins; the final bin contains every incident at 120 minutes or longer.",
    x = "Reported delay minutes", y = "Incidents",
    caption = "Source: City of Toronto TTC delay data, 2014-2026."
  ) +
  theme_ttc()
save_figure(p5, "fig05_delay_distribution.png", width = 10, height = 4.8)

# Figure 6: monthly delay minutes ------------------------------------------
p6 <- ggplot(monthly, aes(x = month_start, y = delay_minutes / 1e3,
                          colour = mode)) +
  geom_line(linewidth = 0.75) +
  scale_colour_manual(values = mode_colours) +
  scale_y_continuous(labels = scales::comma) +
  labs(
    title = "Monthly reported delay minutes by mode",
    subtitle = "The final month may be partial; read it with the daily counts in fig01.",
    x = NULL, y = "Thousand delay minutes", colour = NULL,
    caption = "Source: City of Toronto TTC delay data, 2014-2026."
  ) +
  theme_ttc()
save_figure(p6, "fig06_monthly_delay_minutes.png", width = 10, height = 5)

# Figure 7: line concentration ---------------------------------------------
p7 <- ggplot(line_summary, aes(x = delay_rank_in_mode,
                               y = cumulative_pct_of_mode,
                               colour = mode)) +
  geom_line(linewidth = 0.9) +
  scale_colour_manual(values = mode_colours) +
  scale_y_continuous(labels = function(x) paste0(x, "%")) +
  labs(
    title = "How concentrated are delay minutes across lines?",
    subtitle = "Cumulative share of each mode's delay minutes when lines are ranked from most to least delay.",
    x = "Line rank within mode", y = "Cumulative share of delay minutes",
    colour = NULL,
    caption = "Lines with fewer than 100 incidents are excluded. Subway has few lines, so its curve is steep by construction."
  ) +
  theme_ttc()
save_figure(p7, "fig07_line_concentration.png", width = 9, height = 5)

message("EDA complete.")
print(mode_summary)
