"use client";

export function Skeleton({ className = "" }: { className?: string }) {
    return (
        <div className={`animate-pulse bg-gray-700 rounded ${className}`}></div>
    );
}

export function SignalCardSkeleton() {
    return (
        <div className="bg-gray-800 rounded-2xl p-8 shadow-2xl border border-gray-700">
            <div className="flex justify-between items-start mb-6">
                <div>
                    <Skeleton className="h-10 w-32 mb-2" />
                    <Skeleton className="h-4 w-24" />
                </div>
                <Skeleton className="h-8 w-24" />
            </div>

            <div className="grid grid-cols-2 gap-4 mb-8">
                <Skeleton className="h-24 rounded-xl" />
                <Skeleton className="h-24 rounded-xl" />
            </div>

            <div className="space-y-3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
            </div>
        </div>
    );
}

export function ChartSkeleton() {
    return (
        <div className="bg-gray-800 rounded-2xl p-4 shadow-2xl border border-gray-700">
            <Skeleton className="h-6 w-32 mb-4" />
            <Skeleton className="h-[400px] w-full rounded-xl" />
        </div>
    );
}

export function WatchlistSkeleton() {
    return (
        <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
            <Skeleton className="h-6 w-24 mb-4" />
            <div className="space-y-3">
                {[1, 2, 3, 4].map((i) => (
                    <Skeleton key={i} className="h-16 w-full rounded-lg" />
                ))}
            </div>
        </div>
    );
}

export function HistorySkeleton() {
    return (
        <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
            <Skeleton className="h-6 w-40 mb-4" />
            <div className="space-y-2">
                {[1, 2, 3, 4, 5].map((i) => (
                    <Skeleton key={i} className="h-12 w-full" />
                ))}
            </div>
        </div>
    );
}
