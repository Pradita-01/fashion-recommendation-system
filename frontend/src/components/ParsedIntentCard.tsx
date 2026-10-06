interface ParsedIntentCardProps {
  intent: string;
  category: string | null;
  occasion: string | null;
  season: string | null;
  attributes: string[];
  language: string;
  normalizedQuery: string;
}

function formatValue(value: string | null): string {
  if (!value) {
    return "Not specified";
  }

  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatLanguage(language: string): string {
  const languages: Record<string, string> = {
    en: "English",
    hi: "Hindi",
    ta: "Tamil",
    te: "Telugu",
    kn: "Kannada",
    ml: "Malayalam",
    fr: "French",
    de: "German",
    es: "Spanish",
  };

  return languages[language.toLowerCase()] ?? language;
}

interface DetailProps {
  label: string;
  value: string;
}

function Detail({ label, value }: DetailProps) {
  return (
    <div className="rounded-xl bg-slate-50 px-4 py-3 dark:bg-slate-800/60">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
        {label}
      </p>

      <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">
        {value}
      </p>
    </div>
  );
}

export function ParsedIntentCard({
  intent,
  category,
  occasion,
  season,
  attributes,
  language,
  normalizedQuery,
}: ParsedIntentCardProps) {
  const hasAttributes = attributes.length > 0;

  return (
    <section className="mb-8 overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 px-6 py-5 dark:border-slate-800">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
            AI Understanding
          </p>

          <h2 className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">
            Here&apos;s how we understood your request
          </h2>
        </div>

        <span className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
          {formatLanguage(language)}
        </span>
      </div>

      {/* Parsed details */}
      <div className="grid gap-3 px-6 py-5 sm:grid-cols-2 lg:grid-cols-4">
        <Detail
          label="Intent"
          value={formatValue(intent)}
        />

        {category && (
          <Detail
            label="Category"
            value={formatValue(category)}
          />
        )}

        {season && (
          <Detail
            label="Season"
            value={formatValue(season)}
          />
        )}

        {occasion && (
          <Detail
            label="Occasion"
            value={formatValue(occasion)}
          />
        )}
      </div>

      {/* Attributes */}
      {hasAttributes && (
        <div className="px-6 pb-5">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Preferences
          </p>

          <div className="flex flex-wrap gap-2">
            {attributes.map((attribute) => (
              <span
                key={attribute}
                className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
              >
                {formatValue(attribute)}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Interpreted query */}
      <div className="mx-6 mb-6 rounded-2xl border border-slate-100 bg-slate-50 px-5 py-4 dark:border-slate-800 dark:bg-slate-800/40">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          Interpreted search
        </p>

        <p className="mt-1.5 text-sm font-medium text-slate-800 dark:text-slate-200">
          &quot;{normalizedQuery}&quot;
        </p>
      </div>
    </section>
  );
}