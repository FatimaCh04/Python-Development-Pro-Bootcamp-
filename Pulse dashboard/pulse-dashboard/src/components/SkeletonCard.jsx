/**
 * SkeletonCard — shimmer placeholder matching PostCard layout.
 * Uses .shimmer-bg from index.css (defined via tailwind keyframe) instead
 * of animate-pulse so each bar sweeps independently.
 */
export default function SkeletonCard({ showImage = false }) {
  return (
    <div
      className="card-surface rounded-2xl p-5 shadow-card"
      aria-hidden="true"
      role="presentation"
    >
      {/* Author row */}
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-full shimmer-bg shrink-0" />
        <div className="flex flex-col gap-2 flex-1">
          <div className="h-3 w-28 rounded-full shimmer-bg" />
          <div className="h-2.5 w-20 rounded-full shimmer-bg" />
        </div>
      </div>

      {/* Content lines */}
      <div className="flex flex-col gap-2 mb-4">
        <div className="h-3 rounded-full shimmer-bg" />
        <div className="h-3 w-5/6 rounded-full shimmer-bg" />
        <div className="h-3 w-3/4 rounded-full shimmer-bg" />
      </div>

      {/* Optional image placeholder */}
      {showImage && <div className="h-44 rounded-xl shimmer-bg mb-4" />}

      {/* Tag chips */}
      <div className="flex gap-2 mb-4">
        <div className="h-5 w-16 rounded-full shimmer-bg" />
        <div className="h-5 w-20 rounded-full shimmer-bg" />
      </div>

      {/* Action bar */}
      <div className="flex gap-3 pt-3 border-t border-white/[0.06]">
        <div className="h-7 w-16 rounded-full shimmer-bg" />
        <div className="h-7 w-12 rounded-full shimmer-bg" />
      </div>
    </div>
  )
}
