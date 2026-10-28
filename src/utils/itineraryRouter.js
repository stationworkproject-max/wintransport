/**
 * Utility functions for intelligent pedestrian and transit itinerary path generation
 */

function distSq(lat1, lon1, lat2, lon2) {
  // Approximate metric scaling for distance calculation
  const cosLat = Math.cos((lat1 * Math.PI) / 180);
  const dLat = (lat2 - lat1) * 111132;
  const dLon = (lon2 - lon1) * 111132 * cosLat;
  return dLat * dLat + dLon * dLon;
}

// In-memory cache for fast, zero-latency walking route retrieval
const walkingRouteCache = new Map();

/**
 * Fetch real street/sidewalk walking path coordinates using OpenStreetMap pedestrian routing.
 * Follows actual street turns, sidewalks, corners, and pedestrian passages like Google Maps walking mode.
 * - Queries high-accuracy OSM routed-foot engine for real sidewalk/street path.
 * - Connects smoothly from exact start position to station entrance.
 * - Falls back cleanly to direct path if offline.
 */
export async function getWalkingRoute(start, end) {
  if (!start || !end || !start.lat || !start.lon || !end.lat || !end.lon) {
    return [];
  }

  const straightDist = Math.sqrt(distSq(start.lat, start.lon, end.lat, end.lon));
  // If points are basically identical (< 8 meters)
  if (straightDist < 8) {
    return [[start.lat, start.lon], [end.lat, end.lon]];
  }

  // Check in-memory route cache
  const cacheKey = `${start.lat.toFixed(5)},${start.lon.toFixed(5)}->${end.lat.toFixed(5)},${end.lon.toFixed(5)}`;
  if (walkingRouteCache.has(cacheKey)) {
    return walkingRouteCache.get(cacheKey);
  }

  // High-precision OpenStreetMap pedestrian routing (routed-foot)
  // Follows sidewalks, crosswalks, pedestrian zones, and real street turns
  const url = `https://routing.openstreetmap.de/routed-foot/route/v1/foot/${start.lon},${start.lat};${end.lon},${end.lat}?overview=full&geometries=geojson&continue_straight=false`;

  try {
    const res = await fetch(url, {
      signal: AbortSignal.timeout(3500)
    });
    if (res.ok) {
      const data = await res.json();
      if (data.routes && data.routes[0]?.geometry?.coordinates) {
        // GeoJSON coordinates are [lon, lat], Leaflet expects [lat, lon]
        const coords = data.routes[0].geometry.coordinates.map(pt => [pt[1], pt[0]]);
        if (coords.length >= 2) {
          // Prepend exact user start point and append exact station destination point
          // so it connects smoothly from the user's feet to the station door without any gap
          const fullRoute = [[start.lat, start.lon], ...coords, [end.lat, end.lon]];
          walkingRouteCache.set(cacheKey, fullRoute);
          return fullRoute;
        }
      }
    }
  } catch (err) {
    // Network offline or timeout: fall back to direct path
  }

  return [[start.lat, start.lon], [end.lat, end.lon]];
}

/**
 * Extracts the exact high-density transit route polyline segment between
 * the origin boarding station and the destination drop-off station.
 * Enforces monotonic progression through intermediate stops to prevent loop jumps.
 */
export function getTransitRideSegment(line, originStation, dropoffStation, directionIndex = 0, transitShapes = {}) {
  if (!line || !originStation || !dropoffStation) return [];

  const originLat = originStation.lat;
  const originLon = originStation.lon;
  const dropLat = dropoffStation.lat;
  const dropLon = dropoffStation.lon;

  // 1. Identify the ordered list of directional stops for this ride
  let directionalStops = [];
  if (directionIndex === 1) {
    if (line.stops_retour && line.stops_retour.length > 0) {
      directionalStops = line.stops_retour;
    } else if (line.stops_aller && line.stops_aller.length > 0) {
      directionalStops = [...line.stops_aller].reverse();
    } else if (line.stops && line.stops.length > 0) {
      directionalStops = [...line.stops].reverse();
    }
  } else {
    if (line.stops_aller && line.stops_aller.length > 0) {
      directionalStops = line.stops_aller;
    } else if (line.stops && line.stops.length > 0) {
      directionalStops = line.stops;
    }
  }

  // Find sub-slice of stops from originStation to dropoffStation
  let stopAIdx = -1;
  let stopBIdx = -1;
  let minStopADist = Infinity;
  let minStopBDist = Infinity;

  directionalStops.forEach((st, idx) => {
    const dA = distSq(st.lat, st.lon, originLat, originLon);
    if (dA < minStopADist) {
      minStopADist = dA;
      stopAIdx = idx;
    }
    const dB = distSq(st.lat, st.lon, dropLat, dropLon);
    if (dB < minStopBDist) {
      minStopBDist = dB;
      stopBIdx = idx;
    }
  });

  let stopsOnRide = [];
  if (stopAIdx !== -1 && stopBIdx !== -1) {
    if (stopAIdx <= stopBIdx) {
      stopsOnRide = directionalStops.slice(stopAIdx, stopBIdx + 1);
    } else {
      stopsOnRide = directionalStops.slice(stopBIdx, stopAIdx + 1).reverse();
    }
  } else {
    stopsOnRide = [originStation, dropoffStation];
  }

  // 2. Select high-density geometry shape strictly adhering to the requested direction
  const shapeKeys = (directionIndex === 1)
    ? [`${line.id}_1`, `${line.id}_retour`, `${line.id}_1_0`, `${line.id}_retour_0`, line.id]
    : [`${line.id}_0`, `${line.id}_aller`, `${line.id}_0_0`, `${line.id}_aller_0`, line.id];

  let rawShape = null;
  let isOppositeShape = false;

  for (const k of shapeKeys) {
    if (transitShapes && transitShapes[k] && transitShapes[k].length > 1) {
      rawShape = transitShapes[k];
      // If we had to fall back to generic line.id for a direction 1 trip, it is oriented in Aller direction
      if (directionIndex === 1 && k === line.id) {
        isOppositeShape = true;
      }
      break;
    }
  }

  // If raw shape is oriented in reverse, flip it so travel direction is forward
  const orientedShape = (rawShape && isOppositeShape)
    ? [...rawShape].reverse()
    : rawShape;

  if (orientedShape && orientedShape.length > 2 && stopsOnRide.length >= 2) {
    // Monotonic shape projection: find the closest shape index for each consecutive stop
    const shapeIndices = [];
    let lastIdx = 0;

    for (let s = 0; s < stopsOnRide.length; s++) {
      const stop = stopsOnRide[s];
      let bestIdx = lastIdx;
      let bestDist = Infinity;

      // Search within a forward window from lastIdx to avoid leaping backwards on loops
      const searchStart = Math.max(0, lastIdx - 15);
      const searchEnd = orientedShape.length;

      for (let i = searchStart; i < searchEnd; i++) {
        const pt = orientedShape[i];
        const d = distSq(pt[0], pt[1], stop.lat, stop.lon);
        if (d < bestDist) {
          bestDist = d;
          bestIdx = i;
        }
      }

      shapeIndices.push(bestIdx);
      lastIdx = bestIdx;
    }

    const firstShapeIdx = shapeIndices[0];
    const lastShapeIdx = shapeIndices[shapeIndices.length - 1];

    if (firstShapeIdx <= lastShapeIdx) {
      const sliced = orientedShape.slice(firstShapeIdx, lastShapeIdx + 1);
      if (sliced.length >= 2) {
        return [[originLat, originLon], ...sliced, [dropLat, dropLon]];
      }
    } else {
      const sliced = orientedShape.slice(lastShapeIdx, firstShapeIdx + 1).reverse();
      if (sliced.length >= 2) {
        return [[originLat, originLon], ...sliced, [dropLat, dropLon]];
      }
    }
  }

  // 3. Fallback: connect consecutive stops on the ride directly
  if (stopsOnRide.length >= 2) {
    return stopsOnRide.map(s => [s.lat, s.lon]);
  }

  return [[originLat, originLon], [dropLat, dropLon]];
}
