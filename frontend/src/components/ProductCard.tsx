import type { Product } from "../lib/api";

interface ProductCardProps {
  product: Product;
}

export function ProductCard({
  product,
}: ProductCardProps) {
  const price =
    product.price !== null
      ? `$${Number(product.price).toFixed(2)}`
      : null;

  return (
    <article className="group overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm transition duration-300 hover:-translate-y-1 hover:border-gray-300 hover:shadow-xl hover:shadow-gray-200/60">
      {/* Image */}
      <div className="relative overflow-hidden bg-gray-100">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.title}
            className="h-72 w-full object-cover transition duration-500 group-hover:scale-105"
            loading="lazy"
          />
        ) : (
          <div className="flex h-72 items-center justify-center bg-gray-100 text-sm text-gray-400">
            No image available
          </div>
        )}

        {/* Category badge */}
        <div className="absolute left-4 top-4">
          <span className="rounded-full border border-white/60 bg-white/90 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wide text-gray-700 shadow-sm backdrop-blur">
            {product.main_category ?? "Fashion"}
          </span>
        </div>
      </div>

      {/* Product content */}
      <div className="p-5">
        {product.store && (
          <p className="text-xs font-medium uppercase tracking-wider text-gray-400">
            {product.store}
          </p>
        )}

        <h2 className="mt-2 line-clamp-2 min-h-[3.5rem] text-base font-semibold leading-6 text-gray-900 transition group-hover:text-gray-700">
          {product.title}
        </h2>

        <div className="mt-5 flex items-center justify-between border-t border-gray-100 pt-4">
          {/* Price */}
          <div>
            {price ? (
              <span className="text-lg font-bold text-gray-900">
                {price}
              </span>
            ) : (
              <span className="text-sm text-gray-400">
                Price unavailable
              </span>
            )}
          </div>

          {/* Rating */}
          {product.average_rating !== null ? (
            <div className="flex items-center gap-1.5 rounded-full bg-gray-50 px-2.5 py-1.5">
              <span className="text-sm">★</span>

              <span className="text-sm font-semibold text-gray-700">
                {Number(product.average_rating).toFixed(1)}
              </span>

              {product.rating_number !== null && (
                <span className="text-xs text-gray-400">
                  ({product.rating_number})
                </span>
              )}
            </div>
          ) : (
            <span className="text-xs text-gray-400">
              No rating
            </span>
          )}
        </div>
      </div>
    </article>
  );
}