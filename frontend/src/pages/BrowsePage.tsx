import {
  useState,
  type FormEvent,
} from "react";

import { useQuery } from "@tanstack/react-query";

import { ProductGrid } from "../components/ProductGrid";

import {
  fetchProducts,
  searchProducts,
} from "../lib/api";

const PAGE_SIZE = 20;
const SEARCH_PAGE_SIZE = 20;

const LANGUAGE_NAMES: Record<string, string> = {
  en: "English",
  ta: "Tamil",
  hi: "Hindi",
  te: "Telugu",
  kn: "Kannada",
  ml: "Malayalam",
  bn: "Bengali",
  de: "German",
  fr: "French",
  es: "Spanish",
};

export function BrowsePage() {
  const [searchInput, setSearchInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchPage, setSearchPage] = useState(1);

  // -------------------------------------------------------------------------
  // Catalogue browsing
  // -------------------------------------------------------------------------

  const browseQuery = useQuery({
    queryKey: ["products", PAGE_SIZE],

    queryFn: () =>
      fetchProducts(
        PAGE_SIZE,
        0,
      ),

    enabled: searchQuery.length === 0,

    staleTime: 30_000,
  });

  // -------------------------------------------------------------------------
  // Semantic search
  // -------------------------------------------------------------------------

  const searchQueryResult = useQuery({
    queryKey: [
      "semantic-search",
      searchQuery,
      searchPage,
    ],

    queryFn: () =>
      searchProducts(
        searchQuery,
        searchPage,
        SEARCH_PAGE_SIZE,
      ),

    enabled: searchQuery.length > 0,

    staleTime: 30_000,
  });

  const isSearching = searchQuery.length > 0;

  // -------------------------------------------------------------------------
  // Products currently displayed
  // -------------------------------------------------------------------------

  const products = isSearching
    ? searchQueryResult.data?.results.map(
        (result) => result.product,
      ) ?? []
    : browseQuery.data?.items ?? [];

  // -------------------------------------------------------------------------
  // Loading state
  // -------------------------------------------------------------------------

  const isLoading = isSearching
    ? searchQueryResult.isLoading
    : browseQuery.isLoading;

  // -------------------------------------------------------------------------
  // Error state
  // -------------------------------------------------------------------------

  const isError = isSearching
    ? searchQueryResult.isError
    : browseQuery.isError;

  const error = isSearching
    ? searchQueryResult.error
    : browseQuery.error;

  // -------------------------------------------------------------------------
  // Search
  // -------------------------------------------------------------------------

  function handleSearch(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const trimmedQuery = searchInput.trim();

    if (!trimmedQuery) {
      clearSearch();
      return;
    }

    setSearchPage(1);
    setSearchQuery(trimmedQuery);
  }

  // -------------------------------------------------------------------------
  // Clear search
  // -------------------------------------------------------------------------

  function clearSearch() {
    setSearchInput("");
    setSearchQuery("");
    setSearchPage(1);
  }

  // -------------------------------------------------------------------------
  // Pagination
  // -------------------------------------------------------------------------

  function goToPreviousPage() {
    setSearchPage(
      (page) => Math.max(1, page - 1),
    );
  }

  function goToNextPage() {
    if (searchQueryResult.data?.has_next) {
      setSearchPage(
        (page) => page + 1,
      );
    }
  }

  // -------------------------------------------------------------------------
  // Parsed query
  // -------------------------------------------------------------------------

  const parsedQuery = searchQueryResult.data?.parsed_query;

  const languageName =
    parsedQuery?.language
      ? LANGUAGE_NAMES[parsedQuery.language] ??
        parsedQuery.language.toUpperCase()
      : null;

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8">

        {/* Header */}
        <div className="mb-10">
          <p className="text-sm font-semibold uppercase tracking-widest text-gray-400">
            Fashion Search
          </p>

          <h1 className="mt-2 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Find something you love.
          </h1>

          <p className="mt-3 max-w-2xl text-sm leading-6 text-gray-500 sm:text-base">
            Search the Amazon Fashion catalogue using natural-language
            queries powered by multilingual semantic and lexical retrieval.
          </p>
        </div>

        {/* Search bar */}
        <form
          onSubmit={handleSearch}
          className="mb-8"
        >
          <div className="flex flex-col gap-3 sm:flex-row">
            <div className="relative flex-1">
              <input
                type="text"
                value={searchInput}
                onChange={(event) =>
                  setSearchInput(event.target.value)
                }
                placeholder="Try: comfortable beach outfit for summer"
                className="w-full rounded-2xl border border-gray-200 bg-white px-5 py-4 pr-12 text-sm text-gray-900 shadow-sm outline-none transition placeholder:text-gray-400 focus:border-gray-400 focus:ring-2 focus:ring-gray-200"
              />
            </div>

            <button
              type="submit"
              className="rounded-2xl bg-gray-900 px-7 py-4 text-sm font-semibold text-white shadow-sm transition hover:bg-gray-800 active:scale-[0.98]"
            >
              Search
            </button>

            {isSearching && (
              <button
                type="button"
                onClick={clearSearch}
                className="rounded-2xl border border-gray-200 bg-white px-6 py-4 text-sm font-semibold text-gray-700 transition hover:bg-gray-100"
              >
                Clear
              </button>
            )}
          </div>
        </form>

        {/* AI Understanding */}
        {isSearching && parsedQuery && (
          <section className="mb-8 overflow-hidden rounded-3xl border border-gray-200 bg-white shadow-sm">
            <div className="border-b border-gray-100 px-6 py-5">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-widest text-gray-400">
                    AI Understanding
                  </p>

                  <h2 className="mt-1 text-lg font-semibold text-gray-900">
                    Here&apos;s how we understood your request
                  </h2>
                </div>

                {languageName && (
                  <span className="inline-flex w-fit items-center rounded-full bg-gray-100 px-3 py-1.5 text-xs font-semibold text-gray-700">
                    {languageName}
                  </span>
                )}
              </div>
            </div>

            <div className="grid gap-4 px-6 py-6 sm:grid-cols-2 lg:grid-cols-4">

              <div className="rounded-2xl bg-gray-50 p-4">
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                  Intent
                </p>

                <p className="mt-2 text-sm font-semibold capitalize text-gray-900">
                  {parsedQuery.intent}
                </p>
              </div>

              {parsedQuery.category && (
                <div className="rounded-2xl bg-gray-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                    Category
                  </p>

                  <p className="mt-2 text-sm font-semibold capitalize text-gray-900">
                    {parsedQuery.category}
                  </p>
                </div>
              )}

              {parsedQuery.season && (
                <div className="rounded-2xl bg-gray-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                    Season
                  </p>

                  <p className="mt-2 text-sm font-semibold capitalize text-gray-900">
                    {parsedQuery.season}
                  </p>
                </div>
              )}

              {parsedQuery.occasion && (
                <div className="rounded-2xl bg-gray-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                    Occasion
                  </p>

                  <p className="mt-2 text-sm font-semibold capitalize text-gray-900">
                    {parsedQuery.occasion}
                  </p>
                </div>
              )}
            </div>

            {parsedQuery.attributes.length > 0 && (
              <div className="px-6 pb-5">
                <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-gray-400">
                  Attributes
                </p>

                <div className="flex flex-wrap gap-2">
                  {parsedQuery.attributes.map(
                    (attribute) => (
                      <span
                        key={attribute}
                        className="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium capitalize text-gray-700"
                      >
                        {attribute}
                      </span>
                    ),
                  )}
                </div>
              </div>
            )}

            <div className="mx-6 mb-6 rounded-2xl border border-gray-100 bg-gray-50 px-5 py-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                Interpreted search
              </p>

              <p className="mt-2 text-sm font-medium text-gray-800">
                &quot;{parsedQuery.normalized_query}&quot;
              </p>
            </div>
          </section>
        )}

        {/* Search status */}
        {isSearching && searchQueryResult.data && (
          <div className="mb-6 flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-gray-900">
                Search results
              </p>

              <p className="mt-1 text-sm text-gray-500">
                {searchQueryResult.data.total} matching candidates
              </p>
            </div>

            <div className="rounded-full bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-500">
              Hybrid Search
            </div>
          </div>
        )}

        {/* Loading */}
        {isLoading && (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {Array.from({ length: 8 }).map(
              (_, index) => (
                <div
                  key={index}
                  className="h-[430px] animate-pulse rounded-2xl bg-gray-200"
                />
              ),
            )}
          </div>
        )}

        {/* Error */}
        {isError && (
          <div className="rounded-2xl border border-red-200 bg-red-50 px-6 py-10 text-center">
            <p className="text-sm font-semibold text-red-700">
              Something went wrong.
            </p>

            <p className="mt-2 text-sm text-red-500">
              {error instanceof Error
                ? error.message
                : "Unable to load products."}
            </p>
          </div>
        )}

        {/* Results */}
        {!isLoading && !isError && (
          <ProductGrid products={products} />
        )}

        {/* Search pagination */}
        {isSearching &&
          searchQueryResult.data &&
          searchQueryResult.data.total > 0 && (
            <div className="mt-12 flex items-center justify-center gap-3">

              <button
                type="button"
                disabled={searchPage === 1}
                onClick={goToPreviousPage}
                className="rounded-xl border border-gray-200 bg-white px-5 py-2.5 text-sm font-medium text-gray-700 shadow-sm transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Previous
              </button>

              <span className="rounded-xl bg-gray-100 px-4 py-2.5 text-sm font-medium text-gray-600">
                Page {searchPage}
              </span>

              <button
                type="button"
                disabled={!searchQueryResult.data.has_next}
                onClick={goToNextPage}
                className="rounded-xl border border-gray-200 bg-white px-5 py-2.5 text-sm font-medium text-gray-700 shadow-sm transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Next
              </button>

            </div>
          )}

      </div>
    </main>
  );
}
