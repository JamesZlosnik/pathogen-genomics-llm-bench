#!/usr/bin/env Rscript
# aggregate_scores.R
# Reads all completed scorecards and produces summary tables and plots.
#
# Usage:
#   Rscript scoring/aggregate_scores.R
#   Rscript scoring/aggregate_scores.R --scorecard scoring/scorecard_template.csv \
#                                       --outdir scoring/plots
#
# Outputs:
#   scoring/plots/heatmap_model_project.pdf/png
#   scoring/plots/boxplot_by_tier.pdf/png
#   scoring/plots/provider_comparison.pdf/png
#   scoring/plots/test_pass_rate.pdf/png
#   scoring/tables/summary_by_model.tsv
#   scoring/tables/summary_by_project.tsv
#   scoring/tables/leaderboard.tsv

suppressPackageStartupMessages({
  library(optparse)
  library(dplyr)
  library(tidyr)
  library(ggplot2)
  library(readr)
  library(janitor)
  library(RColorBrewer)
  library(scales)
})

# ---------------------------------------------------------------------------
# Args
# ---------------------------------------------------------------------------

option_list <- list(
  make_option("--scorecard",
    default = "scoring/scorecard_template.csv",
    help    = "Path to scorecard CSV [default: %default]"),
  make_option("--outdir",
    default = "scoring/plots",
    help    = "Output directory for plots [default: %default]"),
  make_option("--min_runs",
    type    = "integer",
    default = 1L,
    help    = "Minimum runs per model to include in summaries [default: %default]")
)

opt <- parse_args(OptionParser(option_list = option_list))

dir.create(opt$outdir,                      showWarnings = FALSE, recursive = TRUE)
dir.create("scoring/tables",                showWarnings = FALSE, recursive = TRUE)

# ---------------------------------------------------------------------------
# Project metadata
# ---------------------------------------------------------------------------

project_meta <- tibble::tribble(
  ~project_id, ~project_name,              ~tier, ~tier_label,
  "01",        "FASTA parser",             1L,    "Tier 1 · Floor",
  "02",        "TSV reformatter",          1L,    "Tier 1 · Floor",
  "03",        "Sequence QC filter",       2L,    "Tier 2 · Core",
  "04",        "Assembly stats",           2L,    "Tier 2 · Core",
  "05",        "Coverage depth",           2L,    "Tier 2 · Core",
  "06",        "AMR gene parser",          2L,    "Tier 2 · Core",
  "07",        "MLST batch typer",         2L,    "Tier 2 · Core",
  "08",        "SNP distance matrix",      3L,    "Tier 3 · Advanced",
  "09",        "VCF annotation parser",    3L,    "Tier 3 · Advanced",
  "10",        "Phylo + metadata viz",     3L,    "Tier 3 · Advanced",
  "11",        "Outbreak cluster report",  4L,    "Tier 4 · Expert",
  "12",        "Nextflow QC pipeline",     4L,    "Tier 4 · Expert"
)

tier_colours <- c(
  "Tier 1 · Floor"    = "#E8E8E8",
  "Tier 2 · Core"     = "#BBDEFB",
  "Tier 3 · Advanced" = "#CE93D8",
  "Tier 4 · Expert"   = "#37474F"
)

# ---------------------------------------------------------------------------
# Load and validate scorecard
# ---------------------------------------------------------------------------

message("Reading scorecard: ", opt$scorecard)

if (!file.exists(opt$scorecard)) {
  stop("Scorecard not found: ", opt$scorecard)
}

raw <- read_csv(opt$scorecard, show_col_types = FALSE) |>
  clean_names()

required_cols <- c("date", "model", "harness", "provider", "project_id",
                   "correctness", "code_quality", "domain_appropriateness",
                   "completeness", "autonomous_execution", "total",
                   "tests_passed", "tests_total", "test_pct", "time_minutes")

missing_cols <- setdiff(required_cols, names(raw))
if (length(missing_cols) > 0) {
  stop("Scorecard is missing required columns: ",
       paste(missing_cols, collapse = ", "))
}

# Filter out template/example rows (notes contains "example" or "fabricated")
df <- raw |>
  filter(!grepl("example|fabricated|template", tolower(notes %||% ""))) |>
  mutate(
    project_id = sprintf("%02d", as.integer(project_id)),
    date       = as.Date(date)
  ) |>
  left_join(project_meta, by = "project_id")

message(sprintf("Loaded %d runs across %d models and %d projects",
                nrow(df), n_distinct(df$model), n_distinct(df$project_id)))

if (nrow(df) == 0) {
  message("No non-example runs found. Add real run data to the scorecard and re-run.")
  quit(status = 0)
}

# ---------------------------------------------------------------------------
# Helper: save plot as pdf + png
# ---------------------------------------------------------------------------

save_plot <- function(p, name, width = 10, height = 7) {
  base <- file.path(opt$outdir, name)
  ggsave(paste0(base, ".pdf"), p, width = width, height = height)
  ggsave(paste0(base, ".png"), p, width = width, height = height, dpi = 300)
  message("Saved: ", base, ".pdf / .png")
}

# ---------------------------------------------------------------------------
# 1. Heatmap: model × project, fill = total score
# ---------------------------------------------------------------------------

heatmap_data <- df |>
  group_by(model, project_id, project_name, tier_label) |>
  summarise(mean_total = mean(total, na.rm = TRUE),
            n_runs     = n(), .groups = "drop")

p_heat <- ggplot(heatmap_data,
                 aes(x = reorder(project_name, as.integer(project_id)),
                     y = reorder(model, mean_total),
                     fill = mean_total)) +
  geom_tile(colour = "white", linewidth = 0.5) +
  geom_text(aes(label = ifelse(is.na(mean_total), "–",
                               sprintf("%.0f", mean_total))),
            size = 3, colour = "grey20") +
  scale_fill_gradientn(
    colours  = c("#d73027", "#fee08b", "#1a9850"),
    limits   = c(0, 20),
    na.value = "grey90",
    name     = "Score\n(/20)"
  ) +
  scale_x_discrete(position = "top") +
  labs(
    title    = "PGB-LLM Benchmark — Score Heatmap",
    subtitle = "Mean total score per model × project (max 20)",
    x        = NULL,
    y        = NULL
  ) +
  theme_minimal(base_size = 11) +
  theme(
    axis.text.x      = element_text(angle = 35, hjust = 0, size = 9),
    axis.text.y      = element_text(size = 9),
    panel.grid       = element_blank(),
    plot.title       = element_text(face = "bold"),
    legend.position  = "right"
  )

save_plot(p_heat, "heatmap_model_project", width = 13, height = max(5, n_distinct(df$model) * 0.6 + 2))

# ---------------------------------------------------------------------------
# 2. Boxplot: score distribution by difficulty tier
# ---------------------------------------------------------------------------

p_tier <- ggplot(df, aes(x = tier_label, y = total, fill = tier_label)) +
  geom_boxplot(outlier.shape = 21, outlier.size = 2, alpha = 0.85) +
  geom_jitter(width = 0.15, alpha = 0.5, size = 1.5, colour = "grey30") +
  scale_fill_manual(values = tier_colours, guide = "none") +
  scale_y_continuous(limits = c(0, 20), breaks = seq(0, 20, 4)) +
  labs(
    title    = "PGB-LLM — Score Distribution by Tier",
    subtitle = "Each point is one model run",
    x        = NULL,
    y        = "Total score (/20)"
  ) +
  theme_minimal(base_size = 12) +
  theme(
    plot.title   = element_text(face = "bold"),
    axis.text.x  = element_text(size = 10)
  )

save_plot(p_tier, "boxplot_by_tier", width = 9, height = 6)

# ---------------------------------------------------------------------------
# 3. Provider comparison: mean score by provider
# ---------------------------------------------------------------------------

provider_data <- df |>
  group_by(provider, project_id, project_name, tier_label) |>
  summarise(mean_total = mean(total, na.rm = TRUE),
            n_runs     = n(), .groups = "drop")

p_prov <- ggplot(provider_data,
                 aes(x = reorder(project_name, as.integer(project_id)),
                     y = mean_total,
                     colour = provider,
                     group  = provider)) +
  geom_line(linewidth = 0.8, alpha = 0.8) +
  geom_point(aes(size = n_runs), alpha = 0.85) +
  scale_colour_brewer(palette = "Set1", name = "Provider") +
  scale_size_continuous(name = "Runs", range = c(2, 5)) +
  scale_y_continuous(limits = c(0, 20), breaks = seq(0, 20, 4)) +
  labs(
    title    = "PGB-LLM — Provider Comparison",
    subtitle = "Mean score per project by inference provider",
    x        = NULL,
    y        = "Mean total score (/20)"
  ) +
  theme_minimal(base_size = 11) +
  theme(
    axis.text.x  = element_text(angle = 35, hjust = 1, size = 9),
    plot.title   = element_text(face = "bold"),
    legend.position = "right"
  )

save_plot(p_prov, "provider_comparison", width = 12, height = 6)

# ---------------------------------------------------------------------------
# 4. Automated test pass rate by model
# ---------------------------------------------------------------------------

test_data <- df |>
  filter(!is.na(tests_passed), !is.na(tests_total), tests_total > 0) |>
  mutate(test_pct = tests_passed / tests_total * 100)

if (nrow(test_data) > 0) {
  p_test <- ggplot(test_data,
                   aes(x = reorder(model, test_pct),
                       y = test_pct,
                       fill = tier_label)) +
    geom_col(alpha = 0.85) +
    geom_hline(yintercept = 100, linetype = "dashed", colour = "grey50") +
    scale_fill_manual(values = tier_colours, name = "Tier") +
    scale_y_continuous(limits = c(0, 105), labels = label_percent(scale = 1)) +
    coord_flip() +
    facet_wrap(~project_name, ncol = 4) +
    labs(
      title    = "PGB-LLM — Automated Test Pass Rate",
      subtitle = "% of pytest tests passed per model × project",
      x        = NULL,
      y        = "Test pass rate (%)"
    ) +
    theme_minimal(base_size = 10) +
    theme(
      plot.title      = element_text(face = "bold"),
      strip.text      = element_text(size = 8),
      legend.position = "bottom"
    )

  save_plot(p_test, "test_pass_rate",
            width  = 14,
            height = max(6, n_distinct(test_data$model) * 0.4 + 3))
} else {
  message("No test pass rate data available — skipping test_pass_rate plot")
}

# ---------------------------------------------------------------------------
# Summary tables
# ---------------------------------------------------------------------------

# By model
summary_model <- df |>
  group_by(model, quantization, harness, provider) |>
  summarise(
    n_runs              = n(),
    n_projects          = n_distinct(project_id),
    mean_total          = round(mean(total, na.rm = TRUE), 1),
    sd_total            = round(sd(total,  na.rm = TRUE), 1),
    mean_correctness    = round(mean(correctness,           na.rm = TRUE), 1),
    mean_code_quality   = round(mean(code_quality,          na.rm = TRUE), 1),
    mean_domain         = round(mean(domain_appropriateness,na.rm = TRUE), 1),
    mean_completeness   = round(mean(completeness,          na.rm = TRUE), 1),
    mean_autonomous     = round(mean(autonomous_execution,  na.rm = TRUE), 1),
    mean_test_pct       = round(mean(test_pct, na.rm = TRUE), 1),
    mean_time_minutes   = round(mean(time_minutes, na.rm = TRUE), 1),
    .groups = "drop"
  ) |>
  arrange(desc(mean_total))

write_tsv(summary_model, "scoring/tables/summary_by_model.tsv")
message("Wrote scoring/tables/summary_by_model.tsv")

# By project
summary_project <- df |>
  group_by(project_id, project_name, tier, tier_label) |>
  summarise(
    n_runs           = n(),
    n_models         = n_distinct(model),
    mean_total       = round(mean(total, na.rm = TRUE), 1),
    sd_total         = round(sd(total,  na.rm = TRUE), 1),
    min_total        = min(total, na.rm = TRUE),
    max_total        = max(total, na.rm = TRUE),
    mean_test_pct    = round(mean(test_pct, na.rm = TRUE), 1),
    .groups = "drop"
  ) |>
  arrange(project_id)

write_tsv(summary_project, "scoring/tables/summary_by_project.tsv")
message("Wrote scoring/tables/summary_by_project.tsv")

# Leaderboard: best score per model across all projects attempted
leaderboard <- df |>
  group_by(model, quantization) |>
  summarise(
    n_projects_attempted = n_distinct(project_id),
    total_score          = sum(total, na.rm = TRUE),
    max_possible         = n_distinct(project_id) * 20,
    pct_of_max           = round(total_score / max_possible * 100, 1),
    mean_per_project     = round(mean(total, na.rm = TRUE), 1),
    mean_test_pct        = round(mean(test_pct, na.rm = TRUE), 1),
    tiers_completed      = paste(sort(unique(
      project_meta$tier_label[project_meta$project_id %in% project_id]
    )), collapse = "; "),
    .groups = "drop"
  ) |>
  arrange(desc(pct_of_max))

write_tsv(leaderboard, "scoring/tables/leaderboard.tsv")
message("Wrote scoring/tables/leaderboard.tsv")

# ---------------------------------------------------------------------------
# Console summary
# ---------------------------------------------------------------------------

cat("\n── PGB-LLM Benchmark Summary ────────────────────────────────\n")
cat(sprintf("  Runs:     %d\n",            nrow(df)))
cat(sprintf("  Models:   %d\n",            n_distinct(df$model)))
cat(sprintf("  Projects: %d / 12\n",       n_distinct(df$project_id)))
cat(sprintf("  Providers: %s\n",           paste(unique(df$provider), collapse = ", ")))
cat(sprintf("  Harnesses: %s\n",           paste(unique(df$harness),  collapse = ", ")))
cat("\n── Top 5 models by mean score ───────────────────────────────\n")
print(head(select(summary_model, model, quantization, n_projects,
                  mean_total, mean_test_pct), 5),
      row.names = FALSE)
cat("─────────────────────────────────────────────────────────────\n\n")
