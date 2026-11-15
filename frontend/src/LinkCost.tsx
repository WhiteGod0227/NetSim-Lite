import { useEffect, useState } from "react";

export default function LinkCost({
  value,
  onCommit,
  onInvalid,
}: {
  value: number;
  onCommit: (value: number) => void;
  onInvalid: () => void;
}) {
  const [draft, setDraft] = useState(String(value));
  useEffect(() => setDraft(String(value)), [value]);
  return (
    <input
      type="number"
      min="0"
      step="any"
      value={draft}
      onChange={(event) => setDraft(event.target.value)}
      onBlur={() => {
        const next = Number(draft);
        if (!draft.trim() || !Number.isFinite(next) || next < 0) {
          setDraft(String(value));
          onInvalid();
          return;
        }
        onCommit(next);
      }}
      onKeyDown={(event) => {
        if (event.key === "Enter") event.currentTarget.blur();
      }}
    />
  );
}
