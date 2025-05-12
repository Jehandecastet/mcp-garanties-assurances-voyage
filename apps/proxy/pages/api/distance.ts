import type { NextApiRequest, NextApiResponse } from 'next';
import airports from '@/data/airports.json'; // adapte le chemin selon arborescence

const toRad = (deg: number) => (deg * Math.PI) / 180;

const haversine = (lat1: number, lon1: number, lat2: number, lon2: number): number => {
  const R = 6371; // rayon terrestre en km
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
    Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  const { from, to } = req.query;

  if (!from || !to) {
    return res.status(400).json({ error: 'Missing parameters ?from=XXX&to=YYY' });
  }

  const a1 = airports.find(a => a.code === String(from).toUpperCase());
  const a2 = airports.find(a => a.code === String(to).toUpperCase());

  if (!a1 || !a2) {
    return res.status(404).json({ error: 'Unknown airport code(s)' });
  }

  const distance = haversine(a1.lat, a1.lon, a2.lat, a2.lon);
  return res.status(200).json({ distance: Math.round(distance) });
}
