import {
  type KeyboardEvent,
  type ReactNode,
  useEffect,
  useId,
  useRef,
} from "react";
import { InlineError } from "@/components/general/InlineError";
import { StepNavigation } from "@/components/page-specific/assessment/StepNavigation";
import type { StepError } from "@/interfaces/project.interface";
import { cn } from "@/lib/utils";

/** Elements that handle Enter themselves (a select opens, a button clicks, a link follows). */
const OWN_ENTER_TAGS = new Set(["SELECT", "TEXTAREA", "BUTTON", "A"]);

const CONTROLS = "input:not([type=hidden]), select, textarea, button";

/**
 * Where a step starts: an element marked `data-autofocus`, else the selected choice, else the
 * first visible, enabled control of the answer. Controls marked `data-skip-autofocus` (e.g. the
 * Review step's Edit links) are never chosen, so Enter cannot open another step by accident.
 */
function initialFocus(
  form: HTMLElement,
  body: HTMLElement,
): HTMLElement | null {
  return (
    form.querySelector<HTMLElement>("[data-autofocus]") ??
    body.querySelector<HTMLElement>("input[type=radio]:checked") ??
    Array.from(body.querySelectorAll<HTMLElement>(CONTROLS)).find(
      (element) =>
        !element.closest("[hidden]") &&
        !element.hasAttribute("data-skip-autofocus") &&
        !(element as HTMLInputElement).disabled,
    ) ??
    null
  );
}

/**
 * One question: number, title, helper text, the answer, an inline error, and Back/OK. Enter
 * continues, Shift+Enter goes back. Mounted once per step (keyed by the shell), so it slides in and
 * focuses the answer (see `initialFocus`) on every step change. `focusNext` starts on OK instead.
 */
export function StepFrame({
  number,
  eyebrow,
  title,
  help,
  error,
  pending = false,
  wide = false,
  nextLabel,
  focusNext = false,
  onNext,
  onBack,
  children,
}: {
  number?: number;
  eyebrow?: ReactNode;
  title: ReactNode;
  help?: ReactNode;
  error?: StepError | string | null;
  pending?: boolean;
  wide?: boolean;
  nextLabel?: string;
  focusNext?: boolean;
  onNext: () => void;
  onBack: (() => void) | null;
  children: ReactNode;
}) {
  const formRef = useRef<HTMLFormElement>(null);
  const bodyRef = useRef<HTMLDivElement>(null);
  const titleId = useId();

  useEffect(() => {
    if (formRef.current && bodyRef.current) {
      initialFocus(formRef.current, bodyRef.current)?.focus();
    }
  }, []);

  const handleKeyDown = (event: KeyboardEvent<HTMLFormElement>) => {
    if (event.key !== "Enter" || event.nativeEvent.isComposing) return;
    if (event.shiftKey) {
      event.preventDefault();
      if (!pending) onBack?.();
      return;
    }
    if (OWN_ENTER_TAGS.has((event.target as HTMLElement).tagName)) return;
    event.preventDefault();
    if (!pending) onNext();
  };

  return (
    <form
      ref={formRef}
      noValidate
      aria-labelledby={titleId}
      onKeyDown={handleKeyDown}
      onSubmit={(event) => {
        event.preventDefault();
        if (!pending) onNext();
      }}
      className={cn(
        "flex w-full flex-col gap-6 duration-200 animate-in fade-in slide-in-from-bottom-3 motion-reduce:animate-none",
        wide ? "max-w-layout" : "max-w-2xl",
      )}
    >
      <div className="flex flex-col gap-2">
        {eyebrow && (
          <p className="text-sm font-medium text-muted-foreground">{eyebrow}</p>
        )}
        {number !== undefined && (
          <p className="text-sm font-semibold text-muted-foreground">
            {number} →
          </p>
        )}
        <h1
          id={titleId}
          className="text-2xl font-semibold tracking-tight wrap-break-word sm:text-3xl"
        >
          {title}
        </h1>
        {help && (
          <div className="flex flex-col gap-2 text-muted-foreground">
            {help}
          </div>
        )}
      </div>
      <div ref={bodyRef} className="min-w-0">
        {children}
      </div>
      <InlineError
        message={typeof error === "string" ? error : error?.message}
        title={typeof error === "string" ? null : error?.title}
        action={typeof error === "string" ? null : error?.action}
      />
      <StepNavigation
        onBack={onBack}
        nextLabel={nextLabel}
        pending={pending}
        autoFocus={focusNext}
      />
    </form>
  );
}
