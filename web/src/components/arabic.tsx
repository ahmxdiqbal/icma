import type { ReactElement, ReactNode } from "react";
import { splitArabicRuns } from "@/lib/mixed-script";

interface ArProps {
  children: ReactNode;
  className?: string;
  as?: "span" | "p" | "div";
}

/** Arabic text: isolated right-to-left run in the Arabic face. */
export function Ar({ children, className = "", as: Tag = "span" }: ArProps): ReactElement {
  return (
    <Tag dir="rtl" lang="ar" className={`font-arabic ${className}`}>
      {children}
    </Tag>
  );
}

/** English prose that may quote Arabic; each Arabic run is isolated as RTL. */
export function MixedText({ text }: { text: string }): ReactElement {
  return (
    <>
      {splitArabicRuns(text).map((run, i) =>
        run.arabic ? (
          <Ar key={i} className="text-[1.08em]">
            {run.text}
          </Ar>
        ) : (
          <span key={i}>{run.text}</span>
        ),
      )}
    </>
  );
}
