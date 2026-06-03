import { useRef, useState } from "react";

type Props = {
  onUpload: (file: File) => void;
  loading: boolean;
};

export function Uploader({ onUpload, loading }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [filename, setFilename] = useState<string | null>(null);

  function handleFile(file: File | null | undefined) {
    if (!file) return;
    setFilename(file.name);
    onUpload(file);
  }

  return (
    <div
      className={`uploader ${dragging ? "dragging" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        handleFile(e.dataTransfer.files?.[0]);
      }}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv,text/csv"
        style={{ display: "none" }}
        onChange={(e) => handleFile(e.target.files?.[0])}
      />
      {loading ? (
        <span>Cleaning your file…</span>
      ) : filename ? (
        <span>
          {filename} <em>(click or drop another to replace)</em>
        </span>
      ) : (
        <span>Click or drag a .csv file here</span>
      )}
    </div>
  );
}
