import type { CleaningReport } from "../types";

type Props = {
  report: CleaningReport;
  schema: Record<string, string>;
  previewRows: Record<string, unknown>[];
};

export function CleaningSummary({ report, schema, previewRows }: Props) {
  return (
    <div>
      <div className="stats-row">
        <Stat label="Rows in" value={report.rows_in} />
        <Stat label="Rows out" value={report.rows_out} />
        <Stat label="Duplicates dropped" value={report.duplicates_dropped} />
        <Stat label="Columns" value={report.columns.length} />
      </div>

      <h3>Per-column changes</h3>
      <table className="report-table">
        <thead>
          <tr>
            <th>Column</th>
            <th>Detected as</th>
            <th>Type</th>
            <th>Coerced</th>
            <th>Filled</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>
          {report.columns.map((c) => (
            <tr key={c.name}>
              <td>
                <code>{c.name}</code>
              </td>
              <td>{c.detected_kind}</td>
              <td>{c.final_dtype}</td>
              <td>{c.rows_coerced || ""}</td>
              <td>{c.nulls_filled || ""}</td>
              <td>
                {c.notes.length > 0 && (
                  <ul className="note-list">
                    {c.notes.map((n, i) => (
                      <li key={i}>{n}</li>
                    ))}
                  </ul>
                )}
                {Object.keys(c.labels_collapsed).length > 0 && (
                  <details>
                    <summary>
                      {Object.keys(c.labels_collapsed).length} labels collapsed
                    </summary>
                    <ul className="label-changes">
                      {Object.entries(c.labels_collapsed).map(([orig, fixed]) => (
                        <li key={orig}>
                          <code>{orig}</code> &rarr; <code>{fixed}</code>
                        </li>
                      ))}
                    </ul>
                  </details>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <details className="preview">
        <summary>Preview (first 10 rows)</summary>
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                {Object.keys(schema).map((c) => (
                  <th key={c}>{c}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {previewRows.map((row, i) => (
                <tr key={i}>
                  {Object.keys(schema).map((c) => (
                    <td key={c}>{format(row[c])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="stat">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

function format(v: unknown): string {
  if (v == null) return "—";
  if (typeof v === "number") {
    return Number.isInteger(v) ? v.toLocaleString() : v.toFixed(2);
  }
  return String(v);
}
