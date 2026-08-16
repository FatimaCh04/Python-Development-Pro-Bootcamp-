/**
 * SkeletonComment — shimmer placeholder matching a single Comment row.
 * Used in CommentSection while comments are loading.
 */
export default function SkeletonComment({ depth = 0 }) {
  return (
    <div
      className={depth > 0 ? 'ml-6 pl-4 border-l border-white/[0.08]' : ''}
      aria-hidden="true"
      role="presentation"
    >
      <div className="flex gap-2.5 py-2.5">
        <div className="w-7 h-7 rounded-full shimmer-bg shrink-0" />
        <div className="flex-1 min-w-0 flex flex-col gap-1.5">
          <div className="shimmer-bg rounded-xl px-3 py-2 inline-flex flex-col gap-1.5 max-w-[80%]">
            <div className="h-2.5 w-20 rounded-full bg-surface-3/60" />
            <div className="h-2.5 w-40 rounded-full bg-surface-3/60" />
          </div>
          <div className="h-2 w-14 rounded-full shimmer-bg ml-1" />
        </div>
      </div>
    </div>
  )
}
