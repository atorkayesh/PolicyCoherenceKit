import { Link } from "@tanstack/react-router";
import { WaypointsIcon } from "lucide-react";
import { APP_NAME } from "@/constants/layout.constants";

/** Top bar on every page: the legacy waypoints badge (app.py:404-477) and the app name. */
export function AppHeader() {
  return (
    <header className="flex w-full items-center px-4 pt-5 sm:px-6">
      <Link to="/" className="flex min-w-0 items-center gap-2.5">
        <span
          aria-hidden="true"
          className="flex size-8 shrink-0 items-center justify-center rounded-md bg-[#1f2937] text-[#f5f7fa]"
        >
          <WaypointsIcon className="size-5" />
        </span>
        <span className="text-[0.95rem] leading-tight font-bold tracking-[-0.03em]">
          {APP_NAME}
        </span>
      </Link>
    </header>
  );
}
