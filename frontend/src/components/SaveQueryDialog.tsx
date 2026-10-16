"use client";
import { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";
import { errorMessage } from "@/lib/api";
import { Button, ErrorBox } from "./ui";

interface Props {
  open: boolean;
  onClose: () => void;
  onSave: (title: string, description: string) => Promise<void>;
}

export function SaveQueryDialog({ open, onClose, onSave }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) {
      setTitle("");
      setDescription("");
      setError(null);
      d.showModal();
    } else if (!open && d.open) {
      d.close();
    }
  }, [open]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || saving) return;
    setSaving(true);
    setError(null);
    try {
      await onSave(title.trim(), description.trim());
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <dialog
      ref={ref}
      aria-labelledby="save-query-title"
      onClose={onClose}
      onClick={(e) => e.target === ref.current && onClose()}
      className="m-auto w-full max-w-md rounded-lg bg-white p-0 shadow-xl backdrop:bg-slate-900/40"
    >
      <form onSubmit={submit} className="space-y-4 p-5">
        <div className="flex items-center justify-between">
          <h2 id="save-query-title" className="text-base font-semibold">
            Save query
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded p-1 text-slate-500 hover:bg-slate-100"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div>
          <label htmlFor="sq-title" className="mb-1 block text-sm font-medium">
            Name
          </label>
          <input
            id="sq-title"
            autoFocus
            required
            maxLength={200}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Revenue by region"
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label htmlFor="sq-desc" className="mb-1 block text-sm font-medium">
            Description{" "}
            <span className="font-normal text-slate-400">(optional)</span>
          </label>
          <textarea
            id="sq-desc"
            rows={3}
            maxLength={2000}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>

        {error && <ErrorBox message={error} />}

        <div className="flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={saving || !title.trim()}>
            {saving ? "Saving…" : "Save"}
          </Button>
        </div>
      </form>
    </dialog>
  );
}
