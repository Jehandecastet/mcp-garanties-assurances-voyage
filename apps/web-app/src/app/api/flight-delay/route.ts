
// 8. pages/api/flight-delay/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const flightNumber = searchParams.get('flightNumber');
  const date = searchParams.get('date');

  if (!flightNumber || !date) {
    return NextResponse.json({ error: 'Missing parameters' }, { status: 400 });
  }

  const AERODATABOX_API_KEY = process.env.AERODATABOX_API_KEY;
  const AERODATABOX_BASE_URL = 'https://aerodatabox.p.rapidapi.com';

  try {
    const url = `${AERODATABOX_BASE_URL}/flights/number/${flightNumber}/${date}`;

    const res = await fetch(url, {
      headers: {
        'X-RapidAPI-Key': AERODATABOX_API_KEY || '',
        'X-RapidAPI-Host': 'aerodatabox.p.rapidapi.com'
      }
    });

    const data = await res.json();

    const flight = data?.departures?.[0] || data?.[0];
    const scheduled = new Date(flight?.arrival?.scheduledTimeUtc);
    const actual = new Date(flight?.arrival?.actualTimeUtc);

    const delayMinutes = Math.round((actual.getTime() - scheduled.getTime()) / 60000);
    const cancelNoticeDays = 7;

    return NextResponse.json({ delayMinutes, cancelNoticeDays });
  } catch (err) {
    console.error('API error:', err);
    return NextResponse.json({ error: 'Failed to fetch flight data' }, { status: 500 });
  }
}
