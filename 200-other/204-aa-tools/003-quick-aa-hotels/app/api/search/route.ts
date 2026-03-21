import { NextRequest, NextResponse } from 'next/server';
import { searchHotels, CITIES } from '@/lib/hotels';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const city = searchParams.get('city');
  const checkIn = searchParams.get('checkIn');
  const checkOut = searchParams.get('checkOut');

  // Validate required params
  if (!city || !checkIn || !checkOut) {
    return NextResponse.json(
      { error: 'Missing required parameters: city, checkIn, checkOut' },
      { status: 400 }
    );
  }

  // Validate city
  if (!CITIES[city]) {
    return NextResponse.json(
      { error: `Invalid city. Valid options: ${Object.keys(CITIES).join(', ')}` },
      { status: 400 }
    );
  }

  // Validate date format (YYYY-MM-DD)
  const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
  if (!dateRegex.test(checkIn) || !dateRegex.test(checkOut)) {
    return NextResponse.json(
      { error: 'Invalid date format. Use YYYY-MM-DD' },
      { status: 400 }
    );
  }

  try {
    const results = await searchHotels(city, checkIn, checkOut);
    return NextResponse.json({ results });
  } catch (error) {
    console.error('Search error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Search failed' },
      { status: 500 }
    );
  }
}
