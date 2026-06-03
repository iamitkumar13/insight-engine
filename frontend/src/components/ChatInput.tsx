import { useState } from "react";

type Props = {
  onAsk: (q: string) => void;
  loading: boolean;
};

const SUGGESTIONS = [
  "Which regions have the highest total sales?",
  "Which product has the best profit margin?",
  "Show monthly sales trend",
  "Which regions have high sales but low profit margins?",
];

export function ChatInput({ onAsk, loading }: Props) {
  const [value, setValue] = useState("");

  function submit() {
    const q = value.trim();
    if (!q || loading) return;
    onAsk(q);
  }

  return (
    <div>
      <div className="chat-row">
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") submit();
          }}
          placeholder="Ask in plain English…"
          disabled={loading}
        />
        <button onClick={submit} disabled={loading || !value.trim()}>
          {loading ? "Thinking…" : "Ask"}
        </button>
      </div>
      <div className="suggestions">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            className="chip"
            onClick={() => setValue(s)}
            disabled={loading}
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
