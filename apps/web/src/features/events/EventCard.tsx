import Link from "next/link";
import { Calendar, MapPin, Ticket, Users } from "lucide-react";

interface Event {
  id: string;
  name: string;
  description: string | null;
  venue: string;
  event_date: string;
  capacity: number;
  ticket_price: number;
  is_active: boolean;
}

interface EventCardProps {
  event: Event;
}

export function EventCard({ event }: EventCardProps) {
  const eventDate = new Date(event.event_date);
  const dateStr = eventDate.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
  const timeStr = eventDate.toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
  });
  const priceStr = `INR ${(event.ticket_price / 100).toFixed(0)}`;

  return (
    <Link href={`/events/${event.id}`} className="group block">
      <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-6 hover:bg-white/20 transition-all duration-200 hover:scale-105 hover:shadow-xl cursor-pointer">
        <div className="inline-flex items-center gap-1 bg-purple-500/20 text-purple-200 text-xs font-medium px-3 py-1 rounded-full mb-4">
          <Calendar className="w-3 h-3" />
          {dateStr} at {timeStr}
        </div>

        <h3 className="text-xl font-bold text-white mb-2 group-hover:text-yellow-300 transition-colors">
          {event.name}
        </h3>

        {event.description && (
          <p className="text-purple-200 text-sm mb-4 line-clamp-2">{event.description}</p>
        )}

        <div className="space-y-2 mb-4">
          <div className="flex items-center gap-2 text-purple-300 text-sm">
            <MapPin className="w-4 h-4 flex-shrink-0" />
            <span className="truncate">{event.venue}</span>
          </div>
          <div className="flex items-center gap-2 text-purple-300 text-sm">
            <Users className="w-4 h-4 flex-shrink-0" />
            <span>{event.capacity} seats</span>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1 text-yellow-400 font-bold text-lg">
            <Ticket className="w-4 h-4" />
            {priceStr}
          </div>
          <span className="bg-purple-600 text-white text-sm px-4 py-1.5 rounded-lg group-hover:bg-purple-500 transition-colors">
            Register
          </span>
        </div>
      </div>
    </Link>
  );
}

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
