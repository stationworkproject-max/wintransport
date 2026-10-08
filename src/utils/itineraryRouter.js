/**
 * Utility functions for intelligent pedestrian and transit itinerary path generation
 */

function distSq(lat1, lon1, lat2, lon2) {
  const dLat = (lat2 - lat1);
  const dLon = (lon2 - lon1);
  return dLat * dLat + dLon * dLon;
}

/**
 * Fetch real street/sidewalk walking path coordinates using OSRM Foot Profile.
 * Falls back to straight line [start, end] if offline or times out.
 */
export async function getWalkingRoute(start, end) {
  if (!start || !end || !start.lat || !start.lon || !end.lat || !end.lon) {
    return [];
  }

  const d = Math.sqrt(distSq(start.lat, start.lon, end.lat, end.lon));
  // If points are basically identical (< 15 meters)
  if (d < 0.00015) {
    return [[start.lat, start.lon], [end.lat, end.lon]];
  }

  try {
    const url = `https://router.project-osrm.org/route/v1/foot/${start.lon},${start.lat};${end.lon},${end.lat}?overview=full&geometries=geojson`;
    const res = await fetch(url, {
      signal: AbortSignal.timeout(3000)
    });
    if (res.ok) {
      const data = await res.json();
      if (data.routes && data.routes[0]?.geometry?.coordinates) {
        // GeoJSON coordinates are [lon, lat], Leaflet expects [lat, lon]
        const coords = data.routes[0].geometry.coordinates.map(pt => [pt[1], pt[0]]);
        if (coords.length >= 2) {
          return coords;
        }
      }
    }
  } catch (err) {
    // Graceful fallback to direct line on slow connection or offline
  }

  return [[start.lat, start.lon], [end.lat, end.lon]];
}

/**
 * Extracts the exact high-density transit route polyline segment between
 * the origin boarding station and the destination drop-off station.
 */
export function getTransitRideSegment(line, originStation, dropoffStation, directionIndex = 0, transitShapes = {}) {
  if (!line || !originStation || !dropoffStation) return [];

  const originLat = originStation.lat;
  const originLon = originStation.lon;
  const dropLat = dropoffStation.lat;
  const dropLon = dropoffStation.lon;

  // Check directional or general shapes in transitShapes
  const shapeKeys = [
    `${line.id}_${directionIndex}`,
    line.id,
    `${line.id}_aller`,
    `${line.id}_retour`
  ];

  let rawShape = null;
  for (const k of shapeKeys) {
    if (transitShapes && transitShapes[k] && transitShapes[k].length > 1) {
      rawShape = transitShapes[k];
      break;
    }
  }

  if (rawShape && rawShape.length > 2) {
    let idxA = 0;
    let minA = Infinity;
    let idxB = 0;
    let minB = Infinity;

    for (let i = 0; i < rawShape.length; i++) {
      const pt = rawShape[i];
      const dA = distSq(pt[0], pt[1], originLat, originLon);
      if (dA < minA) {
        minA = dA;
        idxA = i;
      }
      const dB = distSq(pt[0], pt[1], dropLat, dropLon);
      if (dB < minB) {
        minB = dB;
        idxB = i;
      }
    }

    let segment = [];
    if (idxA <= idxB) {
      segment = rawShape.slice(idxA, idxB + 1);
    } else {
      segment = rawShape.slice(idxB, idxA + 1).reverse();
    }

    if (segment.length > 0) {
      // Pin endpoints exactly to origin and dropoff stations
      const result = [[originLat, originLon], ...segment, [dropLat, dropLon]];
      return result;
    }
  }

  // Fallback: use stops list on the line
  const stops = (directionIndex === 1 && line.stops_retour?.length)
    ? line.stops_retour
    : (line.stops_aller?.length ? line.stops_aller : (line.stops || []));

  let stopIdxA = -1;
  let stopIdxB = -1;
  let minStopA = Infinity;
  let minStopB = Infinity;

  stops.forEach((s, idx) => {
    const dA = distSq(s.lat, s.lon, originLat, originLon);
    if (dA < minStopA) { minStopA = dA; stopIdxA = idx; }
    const dB = distSq(s.lat, s.lon, dropLat, dropLon);
    if (dB < minStopB) { minStopB = dB; stopIdxB = idx; }
  });

  if (stopIdxA !== -1 && stopIdxB !== -1) {
    const slicedStops = stopIdxA <= stopIdxB
      ? stops.slice(stopIdxA, stopIdxB + 1)
      : stops.slice(stopIdxB, stopIdxA + 1).reverse();
    return slicedStops.map(s => [s.lat, s.lon]);
  }

  return [[originLat, originLon], [dropLat, dropLon]];
}
