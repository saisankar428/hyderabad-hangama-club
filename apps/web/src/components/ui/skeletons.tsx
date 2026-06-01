export function EventCardSkeleton() {
    return (
        <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-6 animate-pulse">
            <div className="h-5 bg-white/20 rounded-full w-32 mb-4" />
            <div className="h-6 bg-white/20 rounded w-3/4 mb-2" />
            <div className="h-4 bg-white/20 rounded w-full mb-1" />
            <div className="h-4 bg-white/20 rounded w-2/3 mb-4" />
            <div className="h-4 bg-white/20 rounded w-1/2 mb-2" />
            <div className="h-4 bg-white/20 rounded w-1/3 mb-4" />
            <div className="flex justify-between">
                <div className="h-7 bg-white/20 rounded w-24" />
                <div className="h-8 bg-white/20 rounded w-20" />
            </div>
        </div>
    );
}

export function RegistrationFormSkeleton() {
    return (
        <div className="space-y-4 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-24 mb-1" />
            <div className="h-10 bg-gray-200 rounded w-full" />
            <div className="h-4 bg-gray-200 rounded w-24 mb-1" />
            <div className="h-10 bg-gray-200 rounded w-full" />
            <div className="h-4 bg-gray-200 rounded w-24 mb-1" />
            <div className="h-10 bg-gray-200 rounded w-full" />
            <div className="h-12 bg-gray-300 rounded w-full" />
        </div>
    );
}
