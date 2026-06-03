export type ColumnReport = {
  name: string;
  original_dtype: string;
  final_dtype: string;
  detected_kind: string;
  nulls_filled: number;
  rows_coerced: number;
  labels_collapsed: Record<string, string>;
  notes: string[];
};

export type CleaningReport = {
  rows_in: number;
  rows_out: number;
  duplicates_dropped: number;
  columns: ColumnReport[];
};

export type UploadResponse = {
  table: string;
  report: CleaningReport;
  table_schema: Record<string, string>;
  preview_rows: Record<string, unknown>[];
};

export type ChartSpec = {
  type: "bar" | "line" | "pie" | "none";
  x: string | null;
  y: string | null;
  series: string | null;
};

export type QueryResponse = {
  sql: string;
  columns: string[];
  rows: (string | number | null)[][];
  chart_spec: ChartSpec;
  insight: string;
};
