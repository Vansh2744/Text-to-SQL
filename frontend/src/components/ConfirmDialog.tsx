"use client";
import { AlertTriangle } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { errorMessage } from "@/lib/api";
import { Button, ErrorBox } from "./ui";

interface Props {
  open: boolean;
  title: string;
  message: React.ReactNode;
  confirmLabel?: string;
  onClose: () => void;
  /** Throw to keep the dialog open and show the error inside it. */
  onConfirm: () => Promise<void>;
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "Delete",
  onClose,
  onConfirm,
}: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) {
      setError(null);
      d.showModal();
    } else if (!open && d.open) {
      d.close();
    }
  }, [open]);

  const confirm = async () => {
    setBusy(true);
    setError(null);
    try {
      await onConfirm();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <dialog
      ref={ref}
      aria-labelledby="confirm-title"
      onClose={onClose}
      onClick={(e) => e.target === ref.current && !busy && onClose()}
      className="m-auto w-full max-w-sm rounded-lg bg-white p-0 shadow-xl backdrop:bg-slate-900/40"
    >
      <div className="space-y-4 p-5">
        <div className="flex items-start gap-3">
          <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-red-50 text-red-600">
            <AlertTriangle className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <h2 id="confirm-title" className="text-base font-semibold">
              {title}
            </h2>
            <p className="mt-1 break-words text-sm text-slate-600">{message}</p>
          </div>
        </div>

        {error && <ErrorBox message={error} />}

        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="secondary"
            onClick={onClose}
            disabled={busy}
            autoFocus
          >
            Cancel
          </Button>
          <button
            type="button"
            onClick={confirm}
            disabled={busy}
            className="inline-flex items-center rounded-md bg-red-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {busy ? "Deleting…" : confirmLabel}
          </button>
        </div>
      </div>
    </dialog>
  );
}
