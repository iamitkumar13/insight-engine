import { useState } from "react";
import { Uploader } from "./components/Uploader";
import { CleaningSummary } from "./components/CleaningSummary";
import { ChatInput } from "./components/ChatInput";
import { DataTable } from "./components/DataTable";
import { ChartView } from "./components/ChartView";
import { Insight } from "./components/Insight";
import { askQuestion, uploadCsv } from "./api";
import type { UploadResponse, QueryResponse } from "./types";

export default function App() {
  const [upload, setUpload] = useState<UploadResponse | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [result, setResult] = useState<QueryResponse | null>(null);
  const [querying, setQuerying] = useState(false);
  const [queryError, setQueryError] = useState<string | null>(null);

  async function handleUpload(file: File) {
    setUploading(true);
    setUploadError(null);
    setResult(null);
    try {
      const data = await uploadCsv(file);
      setUpload(data);
    } catch (e) {
      setUploadError(e instanceof Error ? e.message : String(e));
    } finally {
      setUploading(false);
    }
  }

  async function handleQuestion(q: string) {
    setQuerying(true);
    setQueryError(null);
    try {
      const data = await askQuestion(q);
      setResult(data);
    } catch (e) {
      setQueryError(e instanceof Error ? e.message : String(e));
    } finally {
      setQuerying(false);
    }
  }

  return (
    <div className="container">
      <header>
        <h1>Insight Engine</h1>
        <p className="subtitle">
          Drop a messy sales CSV, ask a question, see what's hiding in your data.
        </p>
      </header>

      <section className="card">
        <h2>1. Upload your CSV</h2>
        <Uploader onUpload={handleUpload} loading={uploading} />
        {uploadError && <div className="error">{uploadError}</div>}
      </section>

      {upload && (
        <section className="card">
          <h2>2. What we cleaned</h2>
          <CleaningSummary
            report={upload.report}
            schema={upload.table_schema}
            previewRows={upload.preview_rows}
          />
        </section>
      )}

      {upload && (
        <section className="card">
          <h2>3. Ask a question</h2>
          <ChatInput onAsk={handleQuestion} loading={querying} />
          {queryError && <div className="error">{queryError}</div>}
        </section>
      )}

      {result && (
        <section className="card">
          <h2>4. Results</h2>
          <Insight text={result.insight} />
          <div className="result-grid">
            <DataTable columns={result.columns} rows={result.rows} />
            <ChartView
              columns={result.columns}
              rows={result.rows}
              spec={result.chart_spec}
            />
          </div>
          <details className="sql-details">
            <summary>SQL generated</summary>
            <pre>
              <code>{result.sql}</code>
            </pre>
          </details>
        </section>
      )}
    </div>
  );
}
