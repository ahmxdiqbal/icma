import type { ReactElement } from "react";
import type { Source } from "@/lib/schema";

const LICENSE_URLS: Readonly<Record<string, string>> = {
  "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
};

function uniqueSources(sources: readonly Source[]): Source[] {
  return [...new Map(sources.map((s) => [`${s.dataset}|${s.url}`, s])).values()];
}

function SourceLine({ source }: { source: Source }): ReactElement {
  const licenseUrl = LICENSE_URLS[source.license];
  return (
    <p>
      Hadith texts, chains and narrator data from{" "}
      <a href={source.url} className="underline underline-offset-2 hover:text-lapis">
        {source.attribution}
      </a>{" "}
      ({source.dataset}), licensed under{" "}
      {licenseUrl === undefined ? (
        source.license
      ) : (
        <a href={licenseUrl} className="underline underline-offset-2 hover:text-lapis">
          {source.license}
        </a>
      )}
      . Bundle structure and corrections are derived from that data.
    </p>
  );
}

export function AttributionFooter({ sources, note }: { sources: readonly Source[]; note?: string }): ReactElement {
  return (
    <footer className="mt-12 border-t border-rule">
      <div className="mx-auto max-w-[1440px] space-y-1 px-4 py-6 text-[14px] text-ink-muted sm:px-6">
        {uniqueSources(sources).map((s) => (
          <SourceLine key={`${s.dataset}|${s.url}`} source={s} />
        ))}
        {note === undefined ? null : <p>{note}</p>}
      </div>
    </footer>
  );
}
