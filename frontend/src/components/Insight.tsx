type Props = { text: string };

export function Insight({ text }: Props) {
  if (!text) return null;
  return (
    <div className="insight">
      <div className="insight-label">Takeaway</div>
      <p>{text}</p>
    </div>
  );
}
