'use client';

import { useState } from 'react';

interface HotelResult {
  rank: number;
  name: string;
  stars: number;
  rating: number;
  reviews: number;
  price: number;
  miles: number;
  yieldRatio: number;
  bookingUrl: string;
}

const CITIES = [
  { value: 'austin', label: 'Austin, TX' },
  { value: 'dallas', label: 'Dallas, TX' },
  { value: 'houston', label: 'Houston, TX' },
  { value: 'las-vegas', label: 'Las Vegas, NV' },
  { value: 'new-york', label: 'New York, NY' },
  { value: 'boston', label: 'Boston, MA' },
  { value: 'san-francisco', label: 'San Francisco, CA' },
  { value: 'los-angeles', label: 'Los Angeles, CA' },
];

function getDefaultDates() {
  const today = new Date();
  const checkIn = new Date(today);
  checkIn.setDate(today.getDate() + 7);
  const checkOut = new Date(checkIn);
  checkOut.setDate(checkIn.getDate() + 2);

  return {
    checkIn: checkIn.toISOString().split('T')[0],
    checkOut: checkOut.toISOString().split('T')[0],
  };
}

export default function Home() {
  const defaults = getDefaultDates();
  const [city, setCity] = useState('austin');
  const [checkIn, setCheckIn] = useState(defaults.checkIn);
  const [checkOut, setCheckOut] = useState(defaults.checkOut);
  const [results, setResults] = useState<HotelResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResults([]);

    try {
      const res = await fetch(
        `/api/search?city=${city}&checkIn=${checkIn}&checkOut=${checkOut}`
      );
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'Search failed');
      }

      setResults(data.results || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          AA Hotels - Miles Yield Finder
        </h1>
        <p className="text-gray-600 mb-8">
          Find hotels with the best AAdvantage miles per dollar (Premium Member rates)
        </p>

        {/* Search Form */}
        <form onSubmit={handleSearch} className="bg-white rounded-lg shadow p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                City
              </label>
              <select
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
              >
                {CITIES.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Check-in
              </label>
              <input
                type="date"
                value={checkIn}
                onChange={(e) => setCheckIn(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Check-out
              </label>
              <input
                type="date"
                value={checkOut}
                onChange={(e) => setCheckOut(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
              />
            </div>

            <div className="flex items-end">
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 text-white rounded-md px-4 py-2 font-medium hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Searching...' : 'Search Hotels'}
              </button>
            </div>
          </div>
        </form>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-8">
            {error}
          </div>
        )}

        {/* Results Table */}
        {results.length > 0 && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                Top 10 Hotels by Miles/$ (Premium Member)
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      #
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Hotel
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Rating
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Price
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Miles
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      LP/$
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Book
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {results.map((hotel) => (
                    <tr key={hotel.rank} className="hover:bg-gray-50">
                      <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {hotel.rank}
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {hotel.name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {'★'.repeat(hotel.stars)}{'☆'.repeat(5 - hotel.stars)}
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-center">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          {hotel.rating.toFixed(1)}
                        </span>
                        <div className="text-xs text-gray-500 mt-1">
                          {hotel.reviews.toLocaleString()} reviews
                        </div>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                        ${hotel.price.toFixed(0)}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                        {hotel.miles.toLocaleString()}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-right">
                        <span className="text-lg font-bold text-blue-600">
                          {hotel.yieldRatio.toFixed(1)}
                        </span>
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-center">
                        <a
                          href={hotel.bookingUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 font-medium"
                        >
                          Book →
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && results.length === 0 && (
          <div className="text-center text-gray-500 py-12">
            Search for hotels to see results sorted by miles per dollar
          </div>
        )}
      </div>
    </div>
  );
}
