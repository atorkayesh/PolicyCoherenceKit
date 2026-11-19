import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * A validation or request error shown next to the control it belongs to; the legacy message-box
 * title (if any) in bold above the message, and an optional action (for example a link to a step).
 */
export function InlineError({
  message,
  title,
  action,
  className,
}: {
  message: string | null | undefined;
  title?: string | null;
  action?: ReactNode;
  className?: string;
}) {
  if (!message) return null;
  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col gap-1 text-sm text-destructive wrap-break-word",
        className,
      )}
    >
      {title && <p className="font-semibold">{title}</p>}
      <p className="whitespace-pre-line">{message}</p>
      {action}
    </div>
  );
}
