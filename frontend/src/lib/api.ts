const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "/api";

// ---------------------------------------------------------------------------
// Product
// ---------------------------------------------------------------------------

export interface Product {
  id: number;
  parent_asin: string;
  title: string;
  description: string | null;
  main_category: string | null;
  store: string | null;
  price: string | null;
  average_rating: string | null;
  rating_number: number | null;
  image_url: string | null;
  catalog_version_id: number;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Catalogue
// ---------------------------------------------------------------------------

export interface ProductListResponse {
  items: Product[];
  total: number;
}

// ---------------------------------------------------------------------------
// Parsed query
// ---------------------------------------------------------------------------

export interface ParsedQuery {
  intent: string;
  category: string | null;
  occasion: string | null;
  season: string | null;
  attributes: string[];
  language: string;
  normalized_query: string;
}

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------

export interface SearchResult {
  product: Product;
  score: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  page: number;
  page_size: number;
  total: number;
  has_next: boolean;
  parsed_query?: ParsedQuery | null;
}

// ---------------------------------------------------------------------------
// Browse products
// ---------------------------------------------------------------------------

export async function fetchProducts(
  limit = 20,
  offset = 0,
): Promise<ProductListResponse> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });

  const response = await fetch(
    `${API_BASE_URL}/v1/products?${params.toString()}`,
  );

  if (!response.ok) {
    throw new Error("Failed to load products.");
  }

  return response.json();
}

// ---------------------------------------------------------------------------
// Semantic search
// ---------------------------------------------------------------------------

export async function searchProducts(
  query: string,
  page = 1,
  pageSize = 20,
): Promise<SearchResponse> {
  const params = new URLSearchParams({
    q: query,
    page: String(page),
    page_size: String(pageSize),
  });

  const response = await fetch(
    `${API_BASE_URL}/v1/search?${params.toString()}`,
  );

  if (!response.ok) {
    throw new Error("Failed to search products.");
  }

  return response.json();
}
